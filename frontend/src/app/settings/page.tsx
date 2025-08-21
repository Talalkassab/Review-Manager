"use client"

import { useLanguage } from "@/contexts/language-context"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { 
  Settings,
  MessageSquare,
  Globe,
  Bell,
  Key,
  Shield,
  Database,
  Save,
  TestTube
} from "lucide-react"

export default function SettingsPage() {
  const { t, isRTL } = useLanguage()

  return (
    <div className={`p-6 space-y-6 ${isRTL ? "font-cairo" : "font-inter"}`}>
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Settings className="w-6 h-6" />
          {t("settings")}
        </h1>
        <p className="text-slate-600 mt-1">
          إعدادات النظام والتكامل مع الخدمات الخارجية
        </p>
      </div>

      <div className="grid gap-6">
        {/* WhatsApp Settings */}
        <Card>
          <CardHeader>
            <CardTitle className={`flex items-center gap-2 ${isRTL && "flex-row-reverse"}`}>
              <MessageSquare className="w-5 h-5 text-green-600" />
              إعدادات واتساب
            </CardTitle>
            <CardDescription>
              تكوين WhatsApp Business API
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="whatsapp-token">رمز الوصول (Access Token)</Label>
              <Input 
                id="whatsapp-token"
                type="password"
                placeholder="•••••••••••••••••••••••"
                className="font-mono"
              />
            </div>
            <div>
              <Label htmlFor="phone-number">رقم الهاتف التجاري</Label>
              <Input 
                id="phone-number"
                placeholder="+966501234567"
              />
            </div>
            <div>
              <Label htmlFor="webhook-url">رابط Webhook</Label>
              <Input 
                id="webhook-url"
                placeholder="https://your-domain.com/webhook"
                className="font-mono text-sm"
              />
            </div>
            <Button className="bg-green-600 hover:bg-green-700">
              <TestTube className={`w-4 h-4 ${isRTL ? "ml-2" : "mr-2"}`} />
              اختبار الاتصال
            </Button>
          </CardContent>
        </Card>

        {/* OpenRouter AI Settings */}
        <Card>
          <CardHeader>
            <CardTitle className={`flex items-center gap-2 ${isRTL && "flex-row-reverse"}`}>
              <Key className="w-5 h-5 text-purple-600" />
              إعدادات OpenRouter AI
            </CardTitle>
            <CardDescription>
              تكوين مفاتيح API للذكاء الاصطناعي
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="openrouter-key">مفتاح OpenRouter API</Label>
              <Input 
                id="openrouter-key"
                type="password" 
                placeholder="sk-or-v1-•••••••••••••••••••••••"
                className="font-mono"
              />
              <p className="text-xs text-slate-500 mt-1">
                احصل على مفتاحك من openrouter.ai
              </p>
            </div>
            <div>
              <Label htmlFor="primary-model">النموذج الأساسي (العربية)</Label>
              <Input 
                id="primary-model"
                value="anthropic/claude-3.5-haiku"
                readOnly
                className="bg-slate-50"
              />
            </div>
            <div>
              <Label htmlFor="fallback-model">النموذج الاحتياطي (الإنجليزية)</Label>
              <Input 
                id="fallback-model"
                value="openai/gpt-4o-mini"
                readOnly
                className="bg-slate-50"
              />
            </div>
            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="text-sm text-blue-700">
                <strong>التكلفة المقدرة:</strong> $15-50 شهرياً لكل مطعم
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Language & Region */}
        <Card>
          <CardHeader>
            <CardTitle className={`flex items-center gap-2 ${isRTL && "flex-row-reverse"}`}>
              <Globe className="w-5 h-5 text-blue-600" />
              اللغة والمنطقة
            </CardTitle>
            <CardDescription>
              إعدادات اللغة والمنطقة الزمنية
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="default-language">اللغة الافتراضية</Label>
              <select className="w-full px-3 py-2 border border-slate-200 rounded-md">
                <option value="ar">العربية</option>
                <option value="en">English</option>
              </select>
            </div>
            <div>
              <Label htmlFor="timezone">المنطقة الزمنية</Label>
              <select className="w-full px-3 py-2 border border-slate-200 rounded-md">
                <option value="Asia/Riyadh">آسيا/الرياض</option>
                <option value="Asia/Dubai">آسيا/دبي</option>
                <option value="Asia/Kuwait">آسيا/الكويت</option>
              </select>
            </div>
            <div>
              <Label htmlFor="date-format">تنسيق التاريخ</Label>
              <select className="w-full px-3 py-2 border border-slate-200 rounded-md">
                <option value="dd/mm/yyyy">DD/MM/YYYY</option>
                <option value="mm/dd/yyyy">MM/DD/YYYY</option>
                <option value="yyyy-mm-dd">YYYY-MM-DD</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card>
          <CardHeader>
            <CardTitle className={`flex items-center gap-2 ${isRTL && "flex-row-reverse"}`}>
              <Bell className="w-5 h-5 text-amber-600" />
              الإشعارات
            </CardTitle>
            <CardDescription>
              إعدادات التنبيهات والإشعارات
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>إشعارات التعليقات السلبية</Label>
                <p className="text-sm text-slate-500">
                  تلقي تنبيه فوري عند وصول تعليق سلبي
                </p>
              </div>
              <input type="checkbox" defaultChecked className="w-4 h-4" />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label>تقارير يومية</Label>
                <p className="text-sm text-slate-500">
                  ملخص يومي للنشاط والإحصائيات
                </p>
              </div>
              <input type="checkbox" defaultChecked className="w-4 h-4" />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label>تنبيهات النظام</Label>
                <p className="text-sm text-slate-500">
                  إشعارات حول حالة النظام والأخطاء
                </p>
              </div>
              <input type="checkbox" defaultChecked className="w-4 h-4" />
            </div>
          </CardContent>
        </Card>

        {/* Database Backup */}
        <Card>
          <CardHeader>
            <CardTitle className={`flex items-center gap-2 ${isRTL && "flex-row-reverse"}`}>
              <Database className="w-5 h-5 text-slate-600" />
              النسخ الاحتياطي
            </CardTitle>
            <CardDescription>
              إعدادات النسخ الاحتياطي للبيانات
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>تكرار النسخ الاحتياطي</Label>
              <select className="w-full px-3 py-2 border border-slate-200 rounded-md">
                <option value="daily">يومياً</option>
                <option value="weekly">أسبوعياً</option>
                <option value="monthly">شهرياً</option>
              </select>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg">
              <div className="text-sm text-slate-600">
                آخر نسخة احتياطية: 13 أغسطس 2024، 10:30 ص
              </div>
            </div>
            <Button variant="outline">
              إنشاء نسخة احتياطية الآن
            </Button>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Save className={`w-4 h-4 ${isRTL ? "ml-2" : "mr-2"}`} />
            حفظ الإعدادات
          </Button>
        </div>
      </div>
    </div>
  )
}