"use client"

import { useLanguage } from "@/contexts/language-context"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useState, useEffect } from "react"
import api from "@/lib/api"
import { 
  TrendingUp,
  TrendingDown,
  Users,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  Star,
  Calendar,
  Download,
  Filter,
  Loader2,
  AlertTriangle
} from "lucide-react"

interface AnalyticsStats {
  total_customers: number
  customers_today: number
  customers_this_week: number
  customers_this_month: number
  pending_contact: number
  contacted: number
  responded: number
  completed: number
  failed: number
  response_rate: number
  positive_feedback_rate: number
  average_rating?: number
  google_reviews_generated: number
}

export default function AnalyticsPage() {
  const { t, isRTL } = useLanguage()
  const [stats, setStats] = useState<AnalyticsStats | null>(null)
  const [customers, setCustomers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadAnalyticsData()
  }, [])

  const loadAnalyticsData = async () => {
    setLoading(true)
    setError(null)

    try {
      // Load analytics stats
      const statsResult = await api.getAnalyticsStats()
      if (statsResult.error) {
        throw new Error(statsResult.error)
      }
      setStats(statsResult.data)

      // Load customers for recent analytics
      const customersResult = await api.getCustomers()
      if (customersResult.error) {
        console.error('Failed to load customers:', customersResult.error)
      } else {
        setCustomers(customersResult.data || [])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics data')
    } finally {
      setLoading(false)
    }
  }

  // Calculate dynamic metrics from real data
  const getMetrics = () => {
    if (!stats) return []

    return [
      {
        title: isRTL ? "معدل الاستجابة" : "Response Rate",
        value: `${stats.response_rate}%`,
        change: stats.response_rate > 50 ? "+Good" : "Low",
        trend: stats.response_rate > 50 ? "up" : "down",
        icon: MessageSquare,
      },
      {
        title: isRTL ? "إجمالي العملاء" : "Total Customers",
        value: stats.total_customers.toString(),
        change: `+${stats.customers_today} today`,
        trend: "up",
        icon: Users,
      },
      {
        title: isRTL ? "معدل التعليقات الإيجابية" : "Positive Feedback Rate",
        value: `${stats.positive_feedback_rate}%`,
        change: stats.positive_feedback_rate > 70 ? "+Good" : "Average",
        trend: stats.positive_feedback_rate > 70 ? "up" : "down",
        icon: ThumbsUp,
      },
      {
        title: isRTL ? "مراجعات جوجل" : "Google Reviews",
        value: stats.google_reviews_generated.toString(),
        change: "Generated",
        trend: "up",
        icon: Star,
      },
    ]
  }

  // Calculate recent analytics from customer data
  const getRecentAnalytics = () => {
    if (!stats) return []

    return [
      {
        period: isRTL ? "إحصائيات العملاء" : "Customer Statistics",
        customers: stats.total_customers,
        responses: stats.responded + stats.completed,
        positive: Math.round((stats.positive_feedback_rate / 100) * stats.total_customers),
        negative: stats.failed,
        neutral: stats.total_customers - Math.round((stats.positive_feedback_rate / 100) * stats.total_customers) - stats.failed,
        responseRate: `${stats.response_rate}%`,
      },
      {
        period: isRTL ? "حالات الاتصال" : "Contact Status",
        customers: stats.total_customers,
        responses: stats.contacted,
        positive: stats.completed,
        negative: stats.failed,
        neutral: stats.pending_contact,
        responseRate: `${stats.response_rate}%`,
      }
    ]
  }

  // Calculate top feedback from customers
  const getTopFeedback = () => {
    if (!customers.length) return []

    // Get customers with feedback and group by sentiment
    const feedbackCustomers = customers.filter(c => c.feedback_text)
    const positiveFeedbacks = feedbackCustomers.filter(c => c.feedback_sentiment === 'positive')
    const negativeFeedbacks = feedbackCustomers.filter(c => c.feedback_sentiment === 'negative')

    const sampleFeedbacks = []

    // Add some sample positive feedback
    if (positiveFeedbacks.length > 0) {
      sampleFeedbacks.push({
        feedback: isRTL ? "تجربة ممتازة والخدمة رائعة" : "Excellent experience and great service",
        count: positiveFeedbacks.length,
        sentiment: "positive",
      })
    }

    // Add sample negative feedback
    if (negativeFeedbacks.length > 0) {
      sampleFeedbacks.push({
        feedback: isRTL ? "يحتاج بعض التحسين" : "Needs some improvement",
        count: negativeFeedbacks.length,
        sentiment: "negative",
      })
    }

    // Add neutral if we have customers without specific sentiment
    const neutralCount = customers.filter(c => !c.feedback_sentiment || c.feedback_sentiment === 'neutral').length
    if (neutralCount > 0) {
      sampleFeedbacks.push({
        feedback: isRTL ? "تجربة عادية" : "Average experience",
        count: neutralCount,
        sentiment: "neutral",
      })
    }

    return sampleFeedbacks
  }

  const metrics = getMetrics()
  const recentAnalytics = getRecentAnalytics()
  const topFeedback = getTopFeedback()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center gap-2">
          <Loader2 className="w-6 h-6 animate-spin" />
          <span>Loading analytics...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-600 mb-4">{error}</p>
            <Button onClick={loadAnalyticsData} className="w-full">
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className={`p-6 space-y-6 ${isRTL ? "font-cairo" : "font-inter"}`}>
      {/* Header */}
      <div className={`flex items-center justify-between ${isRTL && "flex-row-reverse"}`}>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {t("analytics")}
          </h1>
          <p className="text-slate-600 mt-1">
            {isRTL ? "تحليل شامل لأداء خدمة العملاء والتعليقات" : "Comprehensive analysis of customer service performance and feedback"}
          </p>
        </div>
        <div className={`flex gap-2 ${isRTL && "flex-row-reverse"}`}>
          <Button variant="outline" size="sm" onClick={loadAnalyticsData}>
            <Filter className={`w-4 h-4 ${isRTL ? "ml-1" : "mr-1"}`} />
            {isRTL ? "تحديث" : "Refresh"}
          </Button>
          <Button variant="outline" size="sm">
            <Download className={`w-4 h-4 ${isRTL ? "ml-1" : "mr-1"}`} />
            {isRTL ? "تصدير التقرير" : "Export Report"}
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, index) => (
          <Card key={index} className="hover:shadow-md transition-shadow">
            <CardHeader className={`flex flex-row items-center justify-between space-y-0 pb-2 ${isRTL && "flex-row-reverse"}`}>
              <CardTitle className="text-sm font-medium text-slate-600">
                {metric.title}
              </CardTitle>
              <metric.icon className="w-5 h-5 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <div className={`flex items-center text-xs mt-1 ${isRTL && "flex-row-reverse"}`}>
                {metric.trend === "up" ? (
                  <TrendingUp className="w-3 h-3 text-green-600 mr-1" />
                ) : (
                  <TrendingDown className="w-3 h-3 text-red-600 mr-1" />
                )}
                <span className={metric.trend === "up" ? "text-green-600" : "text-red-600"}>
                  {metric.change}
                </span>
                <span className="text-slate-500 mr-1">من الشهر الماضي</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Period Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className={`flex items-center gap-2 ${isRTL && "flex-row-reverse"}`}>
              <Calendar className="w-5 h-5 text-blue-600" />
              {isRTL ? "إحصائيات العملاء" : "Customer Statistics"}
            </CardTitle>
            <CardDescription>
              {isRTL ? "تفاصيل شاملة حول حالة العملاء والتفاعل" : "Comprehensive details about customer status and interaction"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentAnalytics.map((period, index) => (
              <div key={index} className="p-4 bg-slate-50 rounded-lg">
                <div className={`flex items-center justify-between mb-2 ${isRTL && "flex-row-reverse"}`}>
                  <h4 className="font-medium">{period.period}</h4>
                  <span className="text-sm text-blue-600 font-medium">
                    {period.responseRate}
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-2 text-sm">
                  <div className="text-center">
                    <div className="text-slate-600">{isRTL ? "عملاء" : "Customers"}</div>
                    <div className="font-medium">{period.customers}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-slate-600">{isRTL ? "ردود" : "Responses"}</div>
                    <div className="font-medium">{period.responses}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-green-600">{isRTL ? "إيجابي" : "Positive"}</div>
                    <div className="font-medium">{period.positive}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-red-600">{isRTL ? "سلبي" : "Negative"}</div>
                    <div className="font-medium">{period.negative}</div>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className={`flex items-center gap-2 ${isRTL && "flex-row-reverse"}`}>
              <Star className="w-5 h-5 text-amber-500" />
              {isRTL ? "ملخص التعليقات" : "Feedback Summary"}
            </CardTitle>
            <CardDescription>
              {isRTL ? "تصنيف التعليقات حسب النوع والعدد" : "Feedback classification by type and count"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {topFeedback.map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div className="flex-1">
                  <p className="text-sm font-medium mb-1">"{item.feedback}"</p>
                  <div className={`flex items-center gap-2 ${isRTL && "flex-row-reverse"}`}>
                    <span className="text-xs text-slate-500">
                      {item.count} {isRTL ? "عميل" : "customers"}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      item.sentiment === "positive" 
                        ? "bg-green-100 text-green-700"
                        : item.sentiment === "negative"
                        ? "bg-red-100 text-red-700"
                        : "bg-gray-100 text-gray-700"
                    }`}>
                      {item.sentiment === "positive" ? (isRTL ? "إيجابي" : "Positive") : 
                       item.sentiment === "negative" ? (isRTL ? "سلبي" : "Negative") :
                       (isRTL ? "محايد" : "Neutral")}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Charts Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>{isRTL ? "الرسوم البيانية التفاعلية" : "Interactive Charts"}</CardTitle>
          <CardDescription>
            {isRTL ? "مخططات بيانية تفصيلية لتحليل الأداء (سيتم إضافة Recharts قريباً)" : "Detailed charts for performance analysis (Recharts integration coming soon)"}
          </CardDescription>
        </CardHeader>
        <CardContent className="h-64 flex items-center justify-center bg-slate-50 rounded-lg">
          <div className="text-center">
            <TrendingUp className="w-12 h-12 text-slate-400 mx-auto mb-3" />
            <p className="text-slate-500">
              {isRTL ? "سيتم إضافة المخططات البيانية التفاعلية هنا" : "Interactive charts will be added here"}
            </p>
            <p className="text-xs text-slate-400 mt-2">
              {isRTL ? "البيانات متوفرة من API الحقيقي" : "Data available from real API"}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}