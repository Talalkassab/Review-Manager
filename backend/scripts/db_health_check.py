#!/usr/bin/env python3
"""
Database health check and monitoring script for Restaurant AI Assistant.
Performs comprehensive health checks, performance monitoring, and alerting.
"""
import asyncio
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.logging import get_logger
from app.database import init_database, db_manager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class DatabaseHealthChecker:
    """Comprehensive database health checking and monitoring."""
    
    def __init__(self, detailed_check: bool = False, alert_thresholds: Dict[str, float] = None):
        self.detailed_check = detailed_check
        self.alert_thresholds = alert_thresholds or {
            'connection_pool_usage': 80.0,  # %
            'slow_query_threshold_ms': 1000.0,
            'disk_usage_threshold': 85.0,  # %
            'memory_usage_threshold': 80.0,  # %
            'failed_messages_rate': 10.0,  # %
            'ai_interaction_errors': 5.0,  # %
        }
        self.health_report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'unknown',
            'checks': {},
            'alerts': [],
            'recommendations': []
        }
    
    async def check_database_connectivity(self, session: AsyncSession) -> Dict[str, Any]:
        """Check basic database connectivity and response time."""
        try:
            start_time = time.time()
            result = await session.execute(text("SELECT 1 as connectivity_test"))
            response_time_ms = (time.time() - start_time) * 1000
            
            connectivity_result = result.scalar()
            
            status = {
                'status': 'healthy' if connectivity_result == 1 else 'unhealthy',
                'response_time_ms': round(response_time_ms, 2),
                'details': 'Database connectivity test passed' if connectivity_result == 1 else 'Database connectivity test failed'
            }
            
            if response_time_ms > 500:
                self.health_report['alerts'].append(f"Slow database response time: {response_time_ms:.2f}ms")
            
            return status
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'details': 'Failed to connect to database'
            }
    
    async def check_connection_pool_health(self, session: AsyncSession) -> Dict[str, Any]:
        """Check connection pool status and usage."""
        try:
            pool = db_manager.engine.pool
            
            pool_status = {
                'total_connections': pool.size() + pool.overflow(),
                'active_connections': pool.checkedout(),
                'idle_connections': pool.checkedin(),
                'pool_size': pool.size(),
                'max_overflow': pool.overflow(),
                'usage_percentage': 0.0
            }
            
            if pool_status['total_connections'] > 0:
                pool_status['usage_percentage'] = (pool_status['active_connections'] / pool_status['total_connections']) * 100
            
            status = 'healthy'
            if pool_status['usage_percentage'] > self.alert_thresholds['connection_pool_usage']:
                status = 'warning'
                self.health_report['alerts'].append(f"High connection pool usage: {pool_status['usage_percentage']:.1f}%")
            
            return {
                'status': status,
                'pool_metrics': pool_status
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def check_database_size_and_growth(self, session: AsyncSession) -> Dict[str, Any]:
        """Check database size and growth patterns."""
        try:
            size_query = text("""
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as total_size,
                    pg_database_size(current_database()) as total_size_bytes,
                    (
                        SELECT pg_size_pretty(sum(pg_total_relation_size(schemaname||'.'||tablename))::bigint)
                        FROM pg_tables WHERE schemaname = 'public'
                    ) as tables_size,
                    (
                        SELECT pg_size_pretty(sum(pg_indexes_size(schemaname||'.'||tablename))::bigint)
                        FROM pg_tables WHERE schemaname = 'public'
                    ) as indexes_size
            """)
            
            result = await session.execute(size_query)
            size_data = result.fetchone()
            
            # Check individual table sizes
            table_sizes_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
            """)
            
            table_result = await session.execute(table_sizes_query)
            table_sizes = [
                {
                    'table': f"{row[0]}.{row[1]}",
                    'size': row[2],
                    'size_bytes': row[3]
                }
                for row in table_result.fetchall()
            ]
            
            return {
                'status': 'healthy',
                'database_size': size_data[0],
                'database_size_bytes': size_data[1],
                'tables_size': size_data[2],
                'indexes_size': size_data[3],
                'largest_tables': table_sizes
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def check_query_performance(self, session: AsyncSession) -> Dict[str, Any]:
        """Check for slow queries and performance issues."""
        try:
            # Check for pg_stat_statements extension
            extension_check = text("SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'")
            result = await session.execute(extension_check)
            has_pg_stat_statements = result.fetchone() is not None
            
            if not has_pg_stat_statements:
                return {
                    'status': 'warning',
                    'message': 'pg_stat_statements extension not installed',
                    'recommendation': 'Install pg_stat_statements for query performance monitoring'
                }
            
            # Get slow queries
            slow_queries = text("""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    max_time,
                    stddev_time
                FROM pg_stat_statements
                WHERE mean_time > :threshold
                ORDER BY mean_time DESC
                LIMIT 10
            """)
            
            result = await session.execute(slow_queries, {'threshold': self.alert_thresholds['slow_query_threshold_ms']})
            slow_query_data = [
                {
                    'query': row[0][:100] + '...' if len(row[0]) > 100 else row[0],
                    'calls': row[1],
                    'total_time_ms': round(row[2], 2),
                    'mean_time_ms': round(row[3], 2),
                    'max_time_ms': round(row[4], 2)
                }
                for row in result.fetchall()
            ]
            
            status = 'healthy'
            if slow_query_data:
                status = 'warning'
                self.health_report['alerts'].append(f"Found {len(slow_query_data)} slow queries")
            
            return {
                'status': status,
                'slow_queries_count': len(slow_query_data),
                'slow_queries': slow_query_data
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def check_table_maintenance(self, session: AsyncSession) -> Dict[str, Any]:
        """Check table maintenance status (autovacuum, analyze)."""
        try:
            maintenance_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze,
                    vacuum_count,
                    autovacuum_count,
                    analyze_count,
                    autoanalyze_count
                FROM pg_stat_user_tables
                ORDER BY tablename
            """)
            
            result = await session.execute(maintenance_query)
            maintenance_data = []
            tables_needing_maintenance = []
            
            for row in result.fetchall():
                table_info = {
                    'schema': row[0],
                    'table': row[1],
                    'last_vacuum': row[2].isoformat() if row[2] else None,
                    'last_autovacuum': row[3].isoformat() if row[3] else None,
                    'last_analyze': row[4].isoformat() if row[4] else None,
                    'last_autoanalyze': row[5].isoformat() if row[5] else None,
                    'vacuum_count': row[6],
                    'autovacuum_count': row[7],
                    'analyze_count': row[8],
                    'autoanalyze_count': row[9]
                }
                
                maintenance_data.append(table_info)
                
                # Check if table needs maintenance
                last_activity = max(
                    row[2] or datetime.min,
                    row[3] or datetime.min,
                    row[4] or datetime.min,
                    row[5] or datetime.min
                )
                
                if last_activity < datetime.utcnow() - timedelta(days=7):
                    tables_needing_maintenance.append(row[1])
            
            status = 'healthy'
            if tables_needing_maintenance:
                status = 'warning'
                self.health_report['recommendations'].append(f"Consider manual VACUUM/ANALYZE for tables: {', '.join(tables_needing_maintenance)}")
            
            return {
                'status': status,
                'tables_needing_maintenance': tables_needing_maintenance,
                'maintenance_stats': maintenance_data
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def check_application_health(self, session: AsyncSession) -> Dict[str, Any]:
        """Check application-specific health metrics."""
        try:
            health_metrics = {}
            
            # Check recent message delivery rates
            message_stats_query = text("""
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_messages,
                    COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered_messages,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as messages_24h
                FROM whatsapp_messages
                WHERE created_at > NOW() - INTERVAL '7 days'
            """)
            
            result = await session.execute(message_stats_query)
            message_stats = result.fetchone()
            
            if message_stats[0] > 0:
                failure_rate = (message_stats[1] / message_stats[0]) * 100
                health_metrics['message_failure_rate'] = round(failure_rate, 2)
                
                if failure_rate > self.alert_thresholds['failed_messages_rate']:
                    self.health_report['alerts'].append(f"High message failure rate: {failure_rate:.1f}%")
            
            # Check AI interaction health
            ai_stats_query = text("""
                SELECT 
                    COUNT(*) as total_interactions,
                    COUNT(CASE WHEN requires_review = true THEN 1 END) as requires_review,
                    AVG(confidence_score) as avg_confidence,
                    AVG(processing_time_ms) as avg_processing_time,
                    COUNT(CASE WHEN resulted_in_positive_outcome = true THEN 1 END) as positive_outcomes
                FROM ai_interactions
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """)
            
            result = await session.execute(ai_stats_query)
            ai_stats = result.fetchone()
            
            if ai_stats[0] > 0:
                health_metrics['ai_interactions_24h'] = ai_stats[0]
                health_metrics['ai_avg_confidence'] = round(float(ai_stats[2] or 0), 3)
                health_metrics['ai_avg_processing_time'] = round(float(ai_stats[3] or 0), 2)
                health_metrics['ai_success_rate'] = round((ai_stats[4] / ai_stats[0]) * 100, 2)
                
                error_rate = (ai_stats[1] / ai_stats[0]) * 100
                if error_rate > self.alert_thresholds['ai_interaction_errors']:
                    self.health_report['alerts'].append(f"High AI interaction error rate: {error_rate:.1f}%")
            
            # Check customer satisfaction trends
            satisfaction_query = text("""
                SELECT 
                    COUNT(*) as total_feedback,
                    COUNT(CASE WHEN feedback_sentiment = 'positive' THEN 1 END) as positive_feedback,
                    COUNT(CASE WHEN feedback_sentiment = 'negative' THEN 1 END) as negative_feedback,
                    AVG(rating) as avg_rating
                FROM customers
                WHERE feedback_received_at > NOW() - INTERVAL '7 days'
                AND feedback_text IS NOT NULL
            """)
            
            result = await session.execute(satisfaction_query)
            satisfaction_stats = result.fetchone()
            
            if satisfaction_stats[0] > 0:
                health_metrics['customer_satisfaction'] = {
                    'total_feedback': satisfaction_stats[0],
                    'positive_rate': round((satisfaction_stats[1] / satisfaction_stats[0]) * 100, 2),
                    'negative_rate': round((satisfaction_stats[2] / satisfaction_stats[0]) * 100, 2),
                    'avg_rating': round(float(satisfaction_stats[3] or 0), 2)
                }
            
            return {
                'status': 'healthy',
                'metrics': health_metrics
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def check_data_consistency(self, session: AsyncSession) -> Dict[str, Any]:
        """Check for data consistency issues and orphaned records."""
        try:
            consistency_issues = []
            
            # Check for orphaned customer records
            orphaned_customers_query = text("""
                SELECT COUNT(*) FROM customers c
                LEFT JOIN restaurants r ON c.restaurant_id = r.id
                WHERE r.id IS NULL
            """)
            
            result = await session.execute(orphaned_customers_query)
            orphaned_customers = result.scalar()
            
            if orphaned_customers > 0:
                consistency_issues.append(f"{orphaned_customers} orphaned customer records")
            
            # Check for messages without customers
            orphaned_messages_query = text("""
                SELECT COUNT(*) FROM whatsapp_messages w
                LEFT JOIN customers c ON w.customer_id = c.id
                WHERE c.id IS NULL
            """)
            
            result = await session.execute(orphaned_messages_query)
            orphaned_messages = result.scalar()
            
            if orphaned_messages > 0:
                consistency_issues.append(f"{orphaned_messages} orphaned message records")
            
            # Check for campaign recipients without campaigns
            orphaned_recipients_query = text("""
                SELECT COUNT(*) FROM campaign_recipients cr
                LEFT JOIN campaigns c ON cr.campaign_id = c.id
                WHERE c.id IS NULL
            """)
            
            result = await session.execute(orphaned_recipients_query)
            orphaned_recipients = result.scalar()
            
            if orphaned_recipients > 0:
                consistency_issues.append(f"{orphaned_recipients} orphaned campaign recipient records")
            
            status = 'healthy' if not consistency_issues else 'warning'
            
            if consistency_issues:
                self.health_report['alerts'].extend(consistency_issues)
            
            return {
                'status': status,
                'issues_found': len(consistency_issues),
                'issues': consistency_issues
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on health check results."""
        recommendations = []
        
        # Check overall system health
        critical_count = sum(1 for check in self.health_report['checks'].values() if check.get('status') == 'critical')
        warning_count = sum(1 for check in self.health_report['checks'].values() if check.get('status') == 'warning')
        
        if critical_count > 0:
            recommendations.append(f"URGENT: Address {critical_count} critical issues immediately")
        
        if warning_count > 2:
            recommendations.append(f"Consider addressing {warning_count} warning issues during next maintenance window")
        
        # Database size recommendations
        if 'database_size' in self.health_report['checks']:
            db_size_gb = self.health_report['checks']['database_size'].get('database_size_bytes', 0) / (1024**3)
            if db_size_gb > 10:
                recommendations.append("Consider implementing data archiving strategy for large database")
        
        # Performance recommendations
        if 'query_performance' in self.health_report['checks']:
            slow_queries = self.health_report['checks']['query_performance'].get('slow_queries_count', 0)
            if slow_queries > 0:
                recommendations.append(f"Optimize {slow_queries} slow queries for better performance")
        
        return recommendations
    
    async def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check."""
        try:
            logger.info("🔍 Starting comprehensive database health check...")
            
            await init_database()
            
            async with db_manager.get_session() as session:
                # Basic checks (always run)
                self.health_report['checks']['connectivity'] = await self.check_database_connectivity(session)
                self.health_report['checks']['connection_pool'] = await self.check_connection_pool_health(session)
                self.health_report['checks']['application_health'] = await self.check_application_health(session)
                
                # Detailed checks (optional)
                if self.detailed_check:
                    logger.info("Running detailed health checks...")
                    self.health_report['checks']['database_size'] = await self.check_database_size_and_growth(session)
                    self.health_report['checks']['query_performance'] = await self.check_query_performance(session)
                    self.health_report['checks']['table_maintenance'] = await self.check_table_maintenance(session)
                    self.health_report['checks']['data_consistency'] = await self.check_data_consistency(session)
                
                # Generate recommendations
                additional_recommendations = await self.generate_recommendations()
                self.health_report['recommendations'].extend(additional_recommendations)
                
                # Determine overall status
                critical_checks = [check for check in self.health_report['checks'].values() if check.get('status') == 'critical']
                warning_checks = [check for check in self.health_report['checks'].values() if check.get('status') == 'warning']
                
                if critical_checks:
                    self.health_report['overall_status'] = 'critical'
                elif warning_checks:
                    self.health_report['overall_status'] = 'warning'
                else:
                    self.health_report['overall_status'] = 'healthy'
                
                logger.info(f"✅ Health check completed - Status: {self.health_report['overall_status']}")
                
                return self.health_report
                
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            self.health_report['overall_status'] = 'critical'
            self.health_report['checks']['error'] = {
                'status': 'critical',
                'error': str(e)
            }
            return self.health_report
        
        finally:
            await db_manager.close()


async def main():
    """Main health check function with command line arguments."""
    parser = argparse.ArgumentParser(description="Run Restaurant AI Assistant database health check")
    parser.add_argument("--detailed", action="store_true", 
                       help="Run detailed health check including performance analysis")
    parser.add_argument("--output", "-o", type=str, 
                       help="Output health report to JSON file")
    parser.add_argument("--alert-threshold", type=float, default=80.0,
                       help="Connection pool usage alert threshold (default: 80%%)")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Only output errors and warnings")
    
    args = parser.parse_args()
    
    # Configure alert thresholds
    alert_thresholds = {
        'connection_pool_usage': args.alert_threshold,
        'slow_query_threshold_ms': 1000.0,
        'disk_usage_threshold': 85.0,
        'memory_usage_threshold': 80.0,
        'failed_messages_rate': 10.0,
        'ai_interaction_errors': 5.0,
    }
    
    checker = DatabaseHealthChecker(
        detailed_check=args.detailed,
        alert_thresholds=alert_thresholds
    )
    
    health_report = await checker.run_health_check()
    
    # Output results
    if not args.quiet:
        print(f"\n🏥 Database Health Check Report")
        print(f"{'=' * 50}")
        print(f"Overall Status: {health_report['overall_status'].upper()}")
        print(f"Timestamp: {health_report['timestamp']}")
        
        if health_report['alerts']:
            print(f"\n⚠️  Alerts ({len(health_report['alerts'])}):")
            for alert in health_report['alerts']:
                print(f"  • {alert}")
        
        if health_report['recommendations']:
            print(f"\n💡 Recommendations ({len(health_report['recommendations'])}):")
            for rec in health_report['recommendations']:
                print(f"  • {rec}")
        
        print(f"\n📊 Check Results:")
        for check_name, result in health_report['checks'].items():
            status_emoji = {
                'healthy': '✅',
                'warning': '⚠️',
                'critical': '❌',
                'error': '💥'
            }.get(result.get('status'), '❓')
            
            print(f"  {status_emoji} {check_name}: {result.get('status', 'unknown')}")
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(health_report, f, indent=2, default=str)
        logger.info(f"Health report saved to {args.output}")
    
    # Exit with appropriate code
    if health_report['overall_status'] == 'critical':
        sys.exit(2)
    elif health_report['overall_status'] == 'warning':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())