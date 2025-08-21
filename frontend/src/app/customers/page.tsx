"use client"

import { useLanguage } from "@/contexts/language-context"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useState, useEffect } from "react"
import api from "@/lib/api"
import { 
  Users,
  Plus,
  Search,
  Filter,
  Download,
  Upload,
  Phone,
  Mail,
  Calendar,
  MessageSquare,
  CheckCircle,
  Clock,
  AlertCircle,
  Loader2,
  X,
  Send
} from "lucide-react"

interface Customer {
  id: string
  customer_number: string
  first_name?: string
  last_name?: string
  phone_number: string
  email?: string
  visit_date: string
  preferred_language: "ar" | "en"
  status: "pending" | "contacted" | "responded" | "completed"
  feedback_sentiment?: "positive" | "negative" | "neutral"
  created_at: string
  updated_at: string
}

export default function CustomersPage() {
  const { t, isRTL } = useLanguage()
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [newCustomer, setNewCustomer] = useState({
    customer_number: "",
    first_name: "",
    last_name: "",
    phone_number: "",
    email: "",
    visit_date: "",
    preferred_language: "ar" as "ar" | "en"
  })
  const [saving, setSaving] = useState(false)
  const [sendingWhatsApp, setSendingWhatsApp] = useState<string | null>(null)

  useEffect(() => {
    loadCustomers()
  }, [])

  const loadCustomers = async () => {
    setLoading(true)
    setError(null)

    try {
      const result = await api.getCustomers()
      if (result.error) {
        throw new Error(result.error)
      }
      setCustomers(result.data || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load customers')
    } finally {
      setLoading(false)
    }
  }

  const handleAddCustomer = async () => {
    if (!newCustomer.customer_number || !newCustomer.phone_number) {
      alert(isRTL ? "الرجاء إدخال رقم العميل ورقم الهاتف" : "Please enter customer number and phone number")
      return
    }

    setSaving(true)
    try {
      const customerData = {
        ...newCustomer,
        visit_date: newCustomer.visit_date || new Date().toISOString(),
      }

      const result = await api.createCustomer(customerData)
      if (result.error) {
        throw new Error(result.error)
      }

      // Refresh customer list
      await loadCustomers()
      
      // Reset form
      setNewCustomer({
        customer_number: "",
        first_name: "",
        last_name: "",
        phone_number: "",
        email: "",
        visit_date: "",
        preferred_language: "ar"
      })
      setShowAddForm(false)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to add customer')
    } finally {
      setSaving(false)
    }
  }

  const handleSendWhatsApp = async (customer: Customer) => {
    setSendingWhatsApp(customer.id)
    try {
      const result = await api.sendGreetingMessage(customer.id)
      if (result.error) {
        throw new Error(result.error)
      }
      
      const displayName = customer.first_name || `Customer #${customer.customer_number}`
      alert(isRTL 
        ? `تم إرسال رسالة واتساب إلى ${displayName} بنجاح!`
        : `WhatsApp message sent to ${displayName} successfully!`
      )
      
      // Refresh customer list to update status
      await loadCustomers()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to send WhatsApp message')
    } finally {
      setSendingWhatsApp(null)
    }
  }

  const filteredCustomers = customers.filter(customer =>
    customer.customer_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (customer.first_name && customer.first_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (customer.last_name && customer.last_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
    customer.phone_number.includes(searchQuery) ||
    (customer.email && customer.email.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pending":
        return <Clock className="w-4 h-4 text-amber-600" />
      case "contacted":
        return <MessageSquare className="w-4 h-4 text-blue-600" />
      case "responded":
        return <AlertCircle className="w-4 h-4 text-purple-600" />
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-600" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "bg-amber-50 text-amber-700 border-amber-200"
      case "contacted":
        return "bg-blue-50 text-blue-700 border-blue-200"
      case "responded":
        return "bg-purple-50 text-purple-700 border-purple-200"
      case "completed":
        return "bg-green-50 text-green-700 border-green-200"
      default:
        return "bg-gray-50 text-gray-700 border-gray-200"
    }
  }

  const getSentimentIcon = (sentiment?: string) => {
    if (!sentiment) return null
    switch (sentiment) {
      case "positive":
        return "😊"
      case "negative":
        return "😞"
      default:
        return "😐"
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "pending":
        return isRTL ? "في الانتظار" : "Pending"
      case "contacted":
        return isRTL ? "تم التواصل" : "Contacted"
      case "responded":
        return isRTL ? "تم الرد" : "Responded"
      case "completed":
        return isRTL ? "مكتمل" : "Completed"
      default:
        return status
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center gap-2">
          <Loader2 className="w-6 h-6 animate-spin" />
          <span>Loading customers...</span>
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
            <Button onClick={loadCustomers} className="w-full">
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
            {isRTL ? "العملاء" : "Customers"}
          </h1>
          <p className="text-slate-600 mt-1">
            {isRTL ? "إدارة بيانات العملاء والتواصل معهم" : "Manage customer data and communications"}
          </p>
        </div>
        <Button 
          onClick={() => setShowAddForm(true)}
          className="bg-green-600 hover:bg-green-700"
        >
          <Plus className={`w-4 h-4 ${isRTL ? "ml-2" : "mr-2"}`} />
          {isRTL ? "إضافة عميل" : "Add Customer"}
        </Button>
      </div>

      {/* Action Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className={`flex flex-col md:flex-row gap-4 ${isRTL && "md:flex-row-reverse"}`}>
            {/* Search */}
            <div className="relative flex-1">
              <Search className={`absolute top-3 w-4 h-4 text-slate-400 ${isRTL ? "right-3" : "left-3"}`} />
              <Input
                placeholder={isRTL ? "بحث في العملاء..." : "Search customers..."}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={isRTL ? "pr-10" : "pl-10"}
              />
            </div>
            
            {/* Action Buttons */}
            <div className={`flex gap-2 ${isRTL && "flex-row-reverse"}`}>
              <Button variant="outline" size="sm">
                <Filter className={`w-4 h-4 ${isRTL ? "ml-1" : "mr-1"}`} />
                {isRTL ? "تصفية" : "Filter"}
              </Button>
              <Button variant="outline" size="sm">
                <Upload className={`w-4 h-4 ${isRTL ? "ml-1" : "mr-1"}`} />
                {isRTL ? "استيراد" : "Import"}
              </Button>
              <Button variant="outline" size="sm">
                <Download className={`w-4 h-4 ${isRTL ? "ml-1" : "mr-1"}`} />
                {isRTL ? "تصدير" : "Export"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Customer List */}
      <div className="grid gap-4">
        {filteredCustomers.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <Users className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-600 mb-2">
                  {isRTL ? "لا يوجد عملاء" : "No customers found"}
                </h3>
                <p className="text-slate-500 mb-4">
                  {searchQuery 
                    ? (isRTL ? "لم يتم العثور على عملاء مطابقين للبحث" : "No customers match your search")
                    : (isRTL ? "ابدأ بإضافة عملائك الأوائل" : "Start by adding your first customers")
                  }
                </p>
                {!searchQuery && (
                  <Button 
                    onClick={() => setShowAddForm(true)}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <Plus className={`w-4 h-4 ${isRTL ? "ml-2" : "mr-2"}`} />
                    {isRTL ? "إضافة عميل" : "Add Customer"}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredCustomers.map((customer) => (
            <Card key={customer.id} className="hover:shadow-md transition-shadow">
              <CardContent className="pt-6">
                <div className={`flex items-center justify-between ${isRTL && "flex-row-reverse"}`}>
                  <div className={`flex items-center space-x-4 ${isRTL && "space-x-reverse"}`}>
                    <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                      <Users className="w-6 h-6 text-blue-600" />
                    </div>
                    
                    <div>
                      <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                        {customer.first_name 
                          ? `${customer.first_name} ${customer.last_name || ''}`.trim()
                          : `Customer #${customer.customer_number}`}
                        {getSentimentIcon(customer.feedback_sentiment)}
                      </h3>
                      <div className={`flex items-center gap-4 text-sm text-slate-600 mt-1 ${isRTL && "flex-row-reverse"}`}>
                        <div className={`flex items-center gap-1 ${isRTL && "flex-row-reverse"}`}>
                          <Phone className="w-3 h-3" />
                          {customer.phone_number}
                        </div>
                        {customer.email && (
                          <div className={`flex items-center gap-1 ${isRTL && "flex-row-reverse"}`}>
                            <Mail className="w-3 h-3" />
                            {customer.email}
                          </div>
                        )}
                        <div className={`flex items-center gap-1 ${isRTL && "flex-row-reverse"}`}>
                          <Calendar className="w-3 h-3" />
                          {new Date(customer.visit_date).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className={`flex items-center space-x-3 ${isRTL && "space-x-reverse"}`}>
                    <div className={`px-3 py-1 rounded-full border text-xs font-medium flex items-center gap-1 ${getStatusColor(customer.status)} ${isRTL && "flex-row-reverse"}`}>
                      {getStatusIcon(customer.status)}
                      {getStatusText(customer.status)}
                    </div>
                    <div className="flex gap-1">
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleSendWhatsApp(customer)}
                        disabled={sendingWhatsApp === customer.id}
                        className="bg-green-50 hover:bg-green-100 text-green-700 border-green-200"
                      >
                        {sendingWhatsApp === customer.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Send className={`w-4 h-4 ${isRTL ? "ml-1" : "mr-1"}`} />
                        )}
                        {isRTL ? "واتساب" : "WhatsApp"}
                      </Button>
                      <Button variant="outline" size="sm">
                        {isRTL ? "عرض" : "View"}
                      </Button>
                      <Button variant="outline" size="sm">
                        {isRTL ? "تعديل" : "Edit"}
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Add Customer Modal/Form */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <div className={`flex items-center justify-between ${isRTL && "flex-row-reverse"}`}>
                <CardTitle>{isRTL ? "إضافة عميل جديد" : "Add New Customer"}</CardTitle>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setShowAddForm(false)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
              <CardDescription>
                {isRTL ? "أدخل بيانات العميل الجديد" : "Enter new customer information"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="customer_number">
                  {isRTL ? "رقم العميل" : "Customer Number"} *
                </Label>
                <Input 
                  id="customer_number" 
                  value={newCustomer.customer_number}
                  onChange={(e) => setNewCustomer({...newCustomer, customer_number: e.target.value})}
                  placeholder={isRTL ? "أدخل رقم العميل" : "Enter customer number"}
                />
              </div>

              <div>
                <Label htmlFor="first_name">
                  {isRTL ? "الاسم الأول (اختياري)" : "First Name (optional)"}
                </Label>
                <Input 
                  id="first_name" 
                  value={newCustomer.first_name}
                  onChange={(e) => setNewCustomer({...newCustomer, first_name: e.target.value})}
                  placeholder={isRTL ? "أدخل الاسم الأول (اختياري)" : "Enter first name (optional)"}
                />
              </div>
              
              <div>
                <Label htmlFor="last_name">
                  {isRTL ? "اسم العائلة" : "Last Name"}
                </Label>
                <Input 
                  id="last_name" 
                  value={newCustomer.last_name}
                  onChange={(e) => setNewCustomer({...newCustomer, last_name: e.target.value})}
                  placeholder={isRTL ? "أدخل اسم العائلة (اختياري)" : "Enter last name (optional)"}
                />
              </div>
              
              <div>
                <Label htmlFor="phone_number">
                  {isRTL ? "رقم الهاتف" : "Phone Number"} *
                </Label>
                <Input 
                  id="phone_number" 
                  type="tel"
                  value={newCustomer.phone_number}
                  onChange={(e) => setNewCustomer({...newCustomer, phone_number: e.target.value})}
                  placeholder="+966501234567"
                />
              </div>
              
              <div>
                <Label htmlFor="email">
                  {isRTL ? "البريد الإلكتروني" : "Email"}
                </Label>
                <Input 
                  id="email" 
                  type="email"
                  value={newCustomer.email}
                  onChange={(e) => setNewCustomer({...newCustomer, email: e.target.value})}
                  placeholder={isRTL ? "البريد الإلكتروني (اختياري)" : "email@example.com (optional)"}
                />
              </div>
              
              <div>
                <Label htmlFor="visit_date">
                  {isRTL ? "تاريخ الزيارة" : "Visit Date"}
                </Label>
                <Input 
                  id="visit_date" 
                  type="datetime-local"
                  value={newCustomer.visit_date}
                  onChange={(e) => setNewCustomer({...newCustomer, visit_date: e.target.value})}
                />
              </div>

              <div>
                <Label htmlFor="preferred_language">
                  {isRTL ? "اللغة المفضلة" : "Preferred Language"}
                </Label>
                <select 
                  id="preferred_language"
                  value={newCustomer.preferred_language}
                  onChange={(e) => setNewCustomer({...newCustomer, preferred_language: e.target.value as "ar" | "en"})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="ar">{isRTL ? "العربية" : "Arabic"}</option>
                  <option value="en">{isRTL ? "الإنجليزية" : "English"}</option>
                </select>
              </div>

              <div className={`flex gap-2 ${isRTL && "flex-row-reverse"}`}>
                <Button 
                  className="flex-1 bg-green-600 hover:bg-green-700"
                  onClick={handleAddCustomer}
                  disabled={saving}
                >
                  {saving ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Plus className={`w-4 h-4 ${isRTL ? "ml-1" : "mr-1"}`} />
                      {isRTL ? "حفظ" : "Save"}
                    </>
                  )}
                </Button>
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => setShowAddForm(false)}
                  disabled={saving}
                >
                  {isRTL ? "إلغاء" : "Cancel"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}