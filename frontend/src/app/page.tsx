"use client"

import { useLanguage } from "@/contexts/language-context"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useState, useEffect } from "react"
import api from "@/lib/api"
import { 
  Users, 
  TrendingUp, 
  MessageSquare, 
  Clock,
  ThumbsUp,
  AlertTriangle,
  Star,
  Phone,
  Loader2
} from "lucide-react"

interface DashboardStats {
  totalCustomers: string
  responseRate: string
  positiveReviews: string
  pendingFollowup: string
}

interface RecentFeedback {
  customer: string
  phone: string
  feedback: string
  sentiment: "positive" | "negative" | "neutral"
  time: string
}

export default function Dashboard() {
  const { t, isRTL } = useLanguage()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentFeedback, setRecentFeedback] = useState<RecentFeedback[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    setError(null)

    try {
      // Load dashboard stats
      const statsResult = await api.getDashboardStats()
      if (statsResult.error) {
        throw new Error(statsResult.error)
      }
      setStats(statsResult.data || null)

      // Load recent feedback
      const feedbackResult = await api.getRecentFeedback()
      if (feedbackResult.error) {
        console.error('Failed to load feedback:', feedbackResult.error)
      } else {
        setRecentFeedback(feedbackResult.data || [])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const statsConfig = [
    {
      title: t("totalCustomers"),
      value: stats?.totalCustomers || "0",
      change: "+0%",
      icon: Users,
      color: "text-blue-600",
    },
    {
      title: t("responseRate"),
      value: stats?.responseRate || "0%",
      change: "+0%",
      icon: MessageSquare,
      color: "text-green-600",
    },
    {
      title: t("positiveReviews"),
      value: stats?.positiveReviews || "0",
      change: "+0%",
      icon: ThumbsUp,
      color: "text-emerald-600",
    },
    {
      title: t("pendingFollowup"),
      value: stats?.pendingFollowup || "0",
      change: "+0%",
      icon: Clock,
      color: "text-amber-600",
    },
  ]

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return <ThumbsUp className="w-4 h-4 text-green-600" />
      case "negative":
        return <AlertTriangle className="w-4 h-4 text-red-600" />
      default:
        return <Star className="w-4 h-4 text-yellow-600" />
    }
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return "border-l-4 border-green-500 bg-green-50"
      case "negative":
        return "border-l-4 border-red-500 bg-red-50"
      default:
        return "border-l-4 border-yellow-500 bg-yellow-50"
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center gap-2">
          <Loader2 className="w-6 h-6 animate-spin" />
          <span>Loading dashboard...</span>
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
            <Button onClick={loadDashboardData} className="w-full">
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
            {t("dashboard")}
          </h1>
          <p className="text-slate-600 mt-1">
            {isRTL ? "مرحباً بك في لوحة التحكم" : "Welcome to your dashboard"}
          </p>
        </div>
        <Button 
          onClick={() => window.location.href = '/customers'}
          className="bg-blue-600 hover:bg-blue-700"
        >
          {t("addCustomer")}
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statsConfig.map((stat, index) => (
          <Card key={index} className="hover:shadow-md transition-shadow">
            <CardHeader className={`flex flex-row items-center justify-between space-y-0 pb-2 ${isRTL && "flex-row-reverse"}`}>
              <CardTitle className="text-sm font-medium text-slate-600">
                {stat.title}
              </CardTitle>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs mt-1 text-slate-500">
                {isRTL ? "البيانات الحالية" : "Current data"}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Feedback */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className={`flex items-center gap-2 ${isRTL && "flex-row-reverse"}`}>
              <MessageSquare className="w-5 h-5 text-blue-600" />
              {isRTL ? "آخر التعليقات" : "Recent Feedback"}
            </CardTitle>
            <CardDescription>
              {isRTL ? "أحدث ردود العملاء على خدماتكم" : "Latest customer feedback on your services"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentFeedback.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                {isRTL ? "لا توجد تعليقات حتى الآن" : "No feedback yet"}
              </div>
            ) : (
              recentFeedback.map((item, index) => (
                <div 
                  key={index}
                  className={`p-4 rounded-lg ${getSentimentColor(item.sentiment)}`}
                >
                  <div className={`flex items-center justify-between mb-2 ${isRTL && "flex-row-reverse"}`}>
                    <div className={`flex items-center gap-2 ${isRTL && "flex-row-reverse"}`}>
                      <span className="font-medium">{item.customer}</span>
                      {getSentimentIcon(item.sentiment)}
                    </div>
                    <div className={`flex items-center gap-1 text-xs text-slate-500 ${isRTL && "flex-row-reverse"}`}>
                      <Phone className="w-3 h-3" />
                      {item.phone}
                    </div>
                  </div>
                  <p className="text-sm text-slate-700 mb-2">
                    "{item.feedback}"
                  </p>
                  <p className="text-xs text-slate-500">{item.time}</p>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>{isRTL ? "إجراءات سريعة" : "Quick Actions"}</CardTitle>
            <CardDescription>
              {isRTL ? "أكثر المهام استخداماً" : "Most used tasks"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button 
              className="w-full justify-start bg-green-600 hover:bg-green-700"
              onClick={() => window.location.href = '/customers'}
            >
              <Users className={`w-4 h-4 ${isRTL ? "ml-2" : "mr-2"}`} />
              {isRTL ? "إضافة عملاء جدد" : "Add New Customers"}
            </Button>
            <Button 
              className="w-full justify-start bg-blue-600 hover:bg-blue-700"
              onClick={() => window.location.href = '/ai-chat'}
            >
              <MessageSquare className={`w-4 h-4 ${isRTL ? "ml-2" : "mr-2"}`} />
              {isRTL ? "إرسال رسائل متابعة" : "Send Follow-up Messages"}
            </Button>
            <Button 
              className="w-full justify-start bg-amber-600 hover:bg-amber-700"
              onClick={loadDashboardData}
            >
              <AlertTriangle className={`w-4 h-4 ${isRTL ? "ml-2" : "mr-2"}`} />
              {isRTL ? "تحديث البيانات" : "Refresh Data"}
            </Button>
            <Button 
              className="w-full justify-start bg-purple-600 hover:bg-purple-700"
              onClick={() => window.location.href = '/analytics'}
            >
              <TrendingUp className={`w-4 h-4 ${isRTL ? "ml-2" : "mr-2"}`} />
              {isRTL ? "عرض التقارير" : "View Reports"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}