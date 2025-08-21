"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { useLanguage } from "@/contexts/language-context"
import { 
  LayoutDashboard, 
  Users, 
  BarChart3, 
  Settings, 
  MessageSquare,
  Globe,
  Store
} from "lucide-react"
import { Button } from "@/components/ui/button"

const navigation = [
  {
    name: "dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    name: "restaurants",
    href: "/restaurants",
    icon: Store,
  },
  {
    name: "customers",
    href: "/customers",
    icon: Users,
  },
  {
    name: "analytics",
    href: "/analytics",
    icon: BarChart3,
  },
  {
    name: "aiAssistant",
    href: "/ai-chat",
    icon: MessageSquare,
  },
  {
    name: "settings",
    href: "/settings",
    icon: Settings,
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const { t, language, setLanguage, isRTL } = useLanguage()

  return (
    <div className={cn(
      "flex h-screen w-64 flex-col bg-slate-900 text-white",
      isRTL && "border-l border-slate-800",
      !isRTL && "border-r border-slate-800"
    )}>
      {/* Logo */}
      <div className="flex h-16 items-center justify-center border-b border-slate-800">
        <h1 className="text-xl font-bold">مساعد المطعم الذكي</h1>
      </div>

      {/* Language Toggle */}
      <div className="flex justify-center p-4 border-b border-slate-800">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setLanguage(language === "ar" ? "en" : "ar")}
          className="text-white border-slate-600 hover:bg-slate-800"
        >
          <Globe className="w-4 h-4 mx-1" />
          {language === "ar" ? "English" : "العربية"}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors",
                isActive
                  ? "bg-slate-800 text-white"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white",
                isRTL && "flex-row-reverse"
              )}
            >
              <item.icon className={cn("w-5 h-5", isRTL ? "ml-3" : "mr-3")} />
              {t(item.name)}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-800">
        <div className="text-xs text-slate-400 text-center">
          {t("language")}: {language === "ar" ? "العربية" : "English"}
        </div>
      </div>
    </div>
  )
}