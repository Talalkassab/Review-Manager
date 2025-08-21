"use client"

import React, { createContext, useContext, useState, useEffect } from "react"

type Language = "ar" | "en"

interface LanguageContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: (key: string) => string
  isRTL: boolean
}

const translations = {
  ar: {
    // Navigation
    dashboard: "لوحة التحكم",
    restaurants: "المطاعم",
    customers: "العملاء",
    analytics: "التحليلات",
    settings: "الإعدادات",
    
    // Customer Management
    addCustomer: "إضافة عميل",
    customerName: "اسم العميل",
    phoneNumber: "رقم الهاتف",
    email: "البريد الإلكتروني",
    visitDate: "تاريخ الزيارة",
    language: "اللغة",
    save: "حفظ",
    cancel: "إلغاء",
    
    // Status
    pending: "قيد الانتظار",
    contacted: "تم التواصل",
    responded: "تم الرد",
    completed: "مكتمل",
    
    // Feedback
    positive: "إيجابي",
    negative: "سلبي",
    neutral: "محايد",
    
    // AI Chat
    aiAssistant: "المساعد الذكي",
    askAI: "اسأل المساعد الذكي...",
    send: "إرسال",
    
    // Dashboard
    totalCustomers: "إجمالي العملاء",
    responseRate: "معدل الاستجابة",
    positiveReviews: "المراجعات الإيجابية",
    pendingFollowup: "متابعة معلقة",
    
    // Common
    search: "بحث",
    filter: "تصفية",
    export: "تصدير",
    import: "استيراد",
    delete: "حذف",
    edit: "تعديل",
    view: "عرض",
  },
  en: {
    // Navigation
    dashboard: "Dashboard",
    restaurants: "Restaurants",
    customers: "Customers", 
    analytics: "Analytics",
    settings: "Settings",
    
    // Customer Management
    addCustomer: "Add Customer",
    customerName: "Customer Name",
    phoneNumber: "Phone Number",
    email: "Email",
    visitDate: "Visit Date",
    language: "Language",
    save: "Save",
    cancel: "Cancel",
    
    // Status
    pending: "Pending",
    contacted: "Contacted",
    responded: "Responded",
    completed: "Completed",
    
    // Feedback
    positive: "Positive",
    negative: "Negative",
    neutral: "Neutral",
    
    // AI Chat
    aiAssistant: "AI Assistant",
    askAI: "Ask AI Assistant...",
    send: "Send",
    
    // Dashboard
    totalCustomers: "Total Customers",
    responseRate: "Response Rate",
    positiveReviews: "Positive Reviews",
    pendingFollowup: "Pending Follow-up",
    
    // Common
    search: "Search",
    filter: "Filter",
    export: "Export",
    import: "Import",
    delete: "Delete",
    edit: "Edit",
    view: "View",
  }
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<Language>("ar") // Arabic is primary

  useEffect(() => {
    // Set HTML dir attribute based on language
    document.documentElement.dir = language === "ar" ? "rtl" : "ltr"
    document.documentElement.lang = language
  }, [language])

  const t = (key: string): string => {
    return translations[language][key as keyof typeof translations["ar"]] || key
  }

  const value = {
    language,
    setLanguage,
    t,
    isRTL: language === "ar",
  }

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (context === undefined) {
    throw new Error("useLanguage must be used within a LanguageProvider")
  }
  return context
}