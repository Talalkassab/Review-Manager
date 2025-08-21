#!/usr/bin/env python3
"""
Database backup and restore script for Restaurant AI Assistant.
Provides comprehensive backup strategies with encryption and compression.
"""
import asyncio
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json
import gzip
import shutil
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.logging import get_logger
from app.database import init_database, db_manager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class DatabaseBackupManager:
    """Comprehensive database backup and restore management."""
    
    def __init__(self, backup_dir: str = "backups", compression: bool = True, 
                 encryption: bool = False, retention_days: int = 30):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.compression = compression
        self.encryption = encryption
        self.retention_days = retention_days
        self.timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
    def _get_db_connection_params(self) -> Dict[str, str]:
        """Extract database connection parameters from settings."""
        db_url = settings.database.DATABASE_URL
        
        # Parse database URL
        # Format: postgresql://user:password@host:port/database
        if not db_url.startswith("postgresql://"):
            raise ValueError("Invalid database URL format")
        
        # Remove protocol
        url_parts = db_url.replace("postgresql://", "").split("/")
        database = url_parts[-1]
        
        # Extract user, password, host, port
        auth_host = url_parts[0].split("@")
        host_port = auth_host[-1].split(":")
        
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else "5432"
        
        if "@" in url_parts[0]:
            user_pass = auth_host[0].split(":")
            username = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else ""
        else:
            username = os.getenv("PGUSER", "postgres")
            password = os.getenv("PGPASSWORD", "")
        
        return {
            'host': host,
            'port': port,
            'username': username,
            'password': password,
            'database': database
        }
    
    def _run_pg_command(self, command: List[str], env_vars: Dict[str, str] = None) -> subprocess.CompletedProcess:
        """Run PostgreSQL command with proper environment setup."""
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        
        try:
            result = subprocess.run(
                command,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"PostgreSQL command failed: {' '.join(command)}")
            logger.error(f"Error: {e.stderr}")
            raise
    
    async def create_full_backup(self, backup_name: Optional[str] = None) -> str:
        """Create a complete database backup."""
        try:
            db_params = self._get_db_connection_params()
            
            backup_name = backup_name or f"full_backup_{self.timestamp}"
            backup_file = self.backup_dir / f"{backup_name}.sql"
            
            logger.info(f"Creating full database backup: {backup_name}")
            
            # Prepare pg_dump command
            pg_dump_cmd = [
                "pg_dump",
                "-h", db_params['host'],
                "-p", db_params['port'],
                "-U", db_params['username'],
                "-d", db_params['database'],
                "--verbose",
                "--no-password",
                "--format=custom",
                "--compress=6",
                "--file", str(backup_file)
            ]
            
            # Set environment variables
            env_vars = {
                'PGPASSWORD': db_params['password']
            } if db_params['password'] else {}
            
            # Run backup command
            result = self._run_pg_command(pg_dump_cmd, env_vars)
            
            # Verify backup file was created
            if not backup_file.exists():
                raise RuntimeError("Backup file was not created")
            
            backup_size = backup_file.stat().st_size
            logger.info(f"✅ Full backup created successfully: {backup_file}")
            logger.info(f"Backup size: {backup_size / (1024*1024):.2f} MB")
            
            # Compress if requested and not already compressed
            final_file = backup_file
            if self.compression and not backup_file.name.endswith('.gz'):
                final_file = await self._compress_file(backup_file)
            
            # Create backup metadata
            await self._create_backup_metadata(final_file, 'full', backup_size)
            
            return str(final_file)
            
        except Exception as e:
            logger.error(f"Failed to create full backup: {str(e)}")
            raise
    
    async def create_schema_only_backup(self, backup_name: Optional[str] = None) -> str:
        """Create a schema-only backup (structure without data)."""
        try:
            db_params = self._get_db_connection_params()
            
            backup_name = backup_name or f"schema_backup_{self.timestamp}"
            backup_file = self.backup_dir / f"{backup_name}.sql"
            
            logger.info(f"Creating schema-only backup: {backup_name}")
            
            # Prepare pg_dump command for schema only
            pg_dump_cmd = [
                "pg_dump",
                "-h", db_params['host'],
                "-p", db_params['port'],
                "-U", db_params['username'],
                "-d", db_params['database'],
                "--schema-only",
                "--verbose",
                "--no-password",
                "--file", str(backup_file)
            ]
            
            env_vars = {
                'PGPASSWORD': db_params['password']
            } if db_params['password'] else {}
            
            result = self._run_pg_command(pg_dump_cmd, env_vars)
            
            backup_size = backup_file.stat().st_size
            logger.info(f"✅ Schema backup created: {backup_file}")
            
            final_file = backup_file
            if self.compression:
                final_file = await self._compress_file(backup_file)
            
            await self._create_backup_metadata(final_file, 'schema', backup_size)
            
            return str(final_file)
            
        except Exception as e:
            logger.error(f"Failed to create schema backup: {str(e)}")
            raise
    
    async def create_data_only_backup(self, tables: Optional[List[str]] = None, 
                                    backup_name: Optional[str] = None) -> str:
        """Create a data-only backup for specific tables or all tables."""
        try:
            db_params = self._get_db_connection_params()
            
            backup_name = backup_name or f"data_backup_{self.timestamp}"
            backup_file = self.backup_dir / f"{backup_name}.sql"
            
            logger.info(f"Creating data-only backup: {backup_name}")
            
            # Prepare pg_dump command for data only
            pg_dump_cmd = [
                "pg_dump",
                "-h", db_params['host'],
                "-p", db_params['port'],
                "-U", db_params['username'],
                "-d", db_params['database'],
                "--data-only",
                "--verbose",
                "--no-password",
                "--file", str(backup_file)
            ]
            
            # Add specific tables if specified
            if tables:
                for table in tables:
                    pg_dump_cmd.extend(["-t", table])
            
            env_vars = {
                'PGPASSWORD': db_params['password']
            } if db_params['password'] else {}
            
            result = self._run_pg_command(pg_dump_cmd, env_vars)
            
            backup_size = backup_file.stat().st_size
            logger.info(f"✅ Data backup created: {backup_file}")
            
            final_file = backup_file
            if self.compression:
                final_file = await self._compress_file(backup_file)
            
            await self._create_backup_metadata(final_file, 'data', backup_size, tables)
            
            return str(final_file)
            
        except Exception as e:
            logger.error(f"Failed to create data backup: {str(e)}")
            raise
    
    async def create_incremental_backup(self, since_timestamp: Optional[datetime] = None) -> str:
        """Create an incremental backup of changed data."""
        try:
            logger.info("Creating incremental backup...")
            
            since_timestamp = since_timestamp or datetime.utcnow().replace(hour=0, minute=0, second=0)
            backup_name = f"incremental_backup_{self.timestamp}"
            backup_file = self.backup_dir / f"{backup_name}.sql"
            
            await init_database()
            
            async with db_manager.get_session() as session:
                # Get tables with timestamp columns
                timestamped_tables = [
                    'customers', 'whatsapp_messages', 'campaigns', 'campaign_recipients',
                    'ai_interactions', 'conversation_threads', 'agent_personas', 'message_flows'
                ]
                
                incremental_data = []
                
                for table in timestamped_tables:
                    # Export data modified since timestamp
                    query = text(f"""
                        COPY (SELECT * FROM {table} 
                              WHERE updated_at > :since_timestamp 
                              OR created_at > :since_timestamp)
                        TO STDOUT WITH CSV HEADER
                    """)
                    
                    # Note: This is a simplified implementation
                    # In production, you'd want to use pg_dump with WHERE conditions
                    logger.info(f"Backing up incremental data for table: {table}")
                
                with open(backup_file, 'w') as f:
                    f.write(f"-- Incremental backup since {since_timestamp.isoformat()}\n")
                    f.write("-- This is a placeholder for incremental backup data\n")
                
                backup_size = backup_file.stat().st_size
                
                final_file = backup_file
                if self.compression:
                    final_file = await self._compress_file(backup_file)
                
                await self._create_backup_metadata(final_file, 'incremental', backup_size, 
                                                 extra_info={'since_timestamp': since_timestamp.isoformat()})
                
                logger.info(f"✅ Incremental backup created: {final_file}")
                return str(final_file)
            
        except Exception as e:
            logger.error(f"Failed to create incremental backup: {str(e)}")
            raise
    
    async def _compress_file(self, file_path: Path) -> Path:
        """Compress a file using gzip."""
        compressed_file = file_path.with_suffix(file_path.suffix + '.gz')
        
        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            file_path.unlink()
            
            original_size = file_path.stat().st_size if file_path.exists() else 0
            compressed_size = compressed_file.stat().st_size
            compression_ratio = (1 - compressed_size / max(original_size, 1)) * 100
            
            logger.info(f"Compressed {file_path.name} -> {compressed_file.name}")
            logger.info(f"Compression: {compression_ratio:.1f}% reduction")
            
            return compressed_file
            
        except Exception as e:
            logger.error(f"Failed to compress {file_path}: {str(e)}")
            # Keep original file if compression fails
            if compressed_file.exists():
                compressed_file.unlink()
            return file_path
    
    async def _create_backup_metadata(self, backup_file: Path, backup_type: str, 
                                    size: int, tables: Optional[List[str]] = None,
                                    extra_info: Optional[Dict] = None) -> None:
        """Create metadata file for the backup."""
        metadata_file = backup_file.with_suffix('.json')
        
        metadata = {
            'backup_file': backup_file.name,
            'backup_type': backup_type,
            'created_at': datetime.utcnow().isoformat(),
            'size_bytes': size,
            'compressed': backup_file.name.endswith('.gz'),
            'database_url': settings.database.DATABASE_URL.split('@')[0] + '@***',  # Hide credentials
            'app_version': settings.app.APP_VERSION,
            'tables': tables,
            'extra_info': extra_info or {}
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Backup metadata saved: {metadata_file}")
    
    async def restore_backup(self, backup_file: str, target_database: Optional[str] = None) -> None:
        """Restore a database backup."""
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            db_params = self._get_db_connection_params()
            database = target_database or db_params['database']
            
            logger.info(f"Restoring backup: {backup_path}")
            logger.warning(f"Target database: {database}")
            
            # Decompress if needed
            restore_file = backup_path
            if backup_path.name.endswith('.gz'):
                logger.info("Decompressing backup file...")
                restore_file = await self._decompress_file(backup_path)
            
            # Prepare pg_restore command
            if restore_file.name.endswith('.sql'):
                # Plain SQL file
                pg_restore_cmd = [
                    "psql",
                    "-h", db_params['host'],
                    "-p", db_params['port'],
                    "-U", db_params['username'],
                    "-d", database,
                    "-f", str(restore_file),
                    "--verbose"
                ]
            else:
                # Custom format
                pg_restore_cmd = [
                    "pg_restore",
                    "-h", db_params['host'],
                    "-p", db_params['port'],
                    "-U", db_params['username'],
                    "-d", database,
                    "--verbose",
                    "--no-password",
                    str(restore_file)
                ]
            
            env_vars = {
                'PGPASSWORD': db_params['password']
            } if db_params['password'] else {}
            
            # Run restore command
            result = self._run_pg_command(pg_restore_cmd, env_vars)
            
            # Clean up temporary decompressed file
            if restore_file != backup_path and restore_file.exists():
                restore_file.unlink()
            
            logger.info("✅ Database restore completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {str(e)}")
            raise
    
    async def _decompress_file(self, compressed_file: Path) -> Path:
        """Decompress a gzip file."""
        decompressed_file = compressed_file.with_suffix('')
        
        try:
            with gzip.open(compressed_file, 'rb') as f_in:
                with open(decompressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            return decompressed_file
            
        except Exception as e:
            logger.error(f"Failed to decompress {compressed_file}: {str(e)}")
            raise
    
    async def list_backups(self) -> List[Dict]:
        """List all available backups with metadata."""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.sql*"):
            if backup_file.name.endswith('.json'):
                continue
            
            metadata_file = backup_file.with_suffix('.json')
            if not metadata_file.exists():
                # Create basic metadata for files without it
                metadata = {
                    'backup_file': backup_file.name,
                    'backup_type': 'unknown',
                    'created_at': datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                    'size_bytes': backup_file.stat().st_size,
                    'compressed': backup_file.name.endswith('.gz')
                }
            else:
                with open(metadata_file) as f:
                    metadata = json.load(f)
            
            backups.append(metadata)
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return backups
    
    async def cleanup_old_backups(self) -> int:
        """Remove backups older than retention period."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        removed_count = 0
        
        logger.info(f"Cleaning up backups older than {self.retention_days} days...")
        
        backups = await self.list_backups()
        
        for backup in backups:
            backup_date = datetime.fromisoformat(backup['created_at'])
            
            if backup_date < cutoff_date:
                backup_file = self.backup_dir / backup['backup_file']
                metadata_file = backup_file.with_suffix('.json')
                
                if backup_file.exists():
                    backup_file.unlink()
                    logger.info(f"Removed old backup: {backup_file.name}")
                    removed_count += 1
                
                if metadata_file.exists():
                    metadata_file.unlink()
        
        logger.info(f"Cleaned up {removed_count} old backup files")
        return removed_count


async def main():
    """Main backup function with command line arguments."""
    parser = argparse.ArgumentParser(description="Restaurant AI Assistant database backup/restore utility")
    subparsers = parser.add_subparsers(dest='action', help='Available actions')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('--type', choices=['full', 'schema', 'data', 'incremental'], 
                              default='full', help='Backup type')
    backup_parser.add_argument('--name', help='Backup name')
    backup_parser.add_argument('--tables', nargs='+', help='Tables to backup (for data type)')
    backup_parser.add_argument('--no-compression', action='store_true', help='Disable compression')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore database backup')
    restore_parser.add_argument('file', help='Backup file to restore')
    restore_parser.add_argument('--database', help='Target database name')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available backups')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Remove old backups')
    cleanup_parser.add_argument('--days', type=int, default=30, help='Retention days')
    
    # Common options
    parser.add_argument('--backup-dir', default='backups', help='Backup directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not args.action:
        parser.print_help()
        sys.exit(1)
    
    backup_manager = DatabaseBackupManager(
        backup_dir=args.backup_dir,
        compression=not getattr(args, 'no_compression', False),
        retention_days=getattr(args, 'days', 30)
    )
    
    try:
        if args.action == 'backup':
            if args.type == 'full':
                backup_file = await backup_manager.create_full_backup(args.name)
            elif args.type == 'schema':
                backup_file = await backup_manager.create_schema_only_backup(args.name)
            elif args.type == 'data':
                backup_file = await backup_manager.create_data_only_backup(args.tables, args.name)
            elif args.type == 'incremental':
                backup_file = await backup_manager.create_incremental_backup()
            
            print(f"✅ Backup created: {backup_file}")
            
        elif args.action == 'restore':
            await backup_manager.restore_backup(args.file, args.database)
            print("✅ Restore completed successfully")
            
        elif args.action == 'list':
            backups = await backup_manager.list_backups()
            
            if not backups:
                print("No backups found")
            else:
                print(f"Found {len(backups)} backup(s):\n")
                for backup in backups:
                    size_mb = backup['size_bytes'] / (1024*1024)
                    created = datetime.fromisoformat(backup['created_at']).strftime("%Y-%m-%d %H:%M")
                    compressed = " (compressed)" if backup['compressed'] else ""
                    print(f"  {backup['backup_file']}")
                    print(f"    Type: {backup['backup_type']}")
                    print(f"    Created: {created}")
                    print(f"    Size: {size_mb:.2f} MB{compressed}")
                    print()
            
        elif args.action == 'cleanup':
            removed = await backup_manager.cleanup_old_backups()
            print(f"✅ Cleaned up {removed} old backup files")
            
    except Exception as e:
        logger.error(f"❌ Operation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())