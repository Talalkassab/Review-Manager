"use client"

import { useLanguage } from "@/contexts/language-context"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useState, useRef, useEffect } from "react"
import { 
  MessageSquare,
  Send,
  Bot,
  User,
  Mic,
  MicOff,
  RefreshCw,
  Sparkles,
  TrendingUp,
  Users,
  AlertTriangle
} from "lucide-react"

interface Message {
  id: string
  type: "user" | "assistant"
  content: string
  timestamp: Date
}

export default function AiChatPage() {
  const { t, isRTL } = useLanguage()
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "assistant",
      content: isRTL 
        ? "مرحباً! أنا مساعدك الذكي. يمكنني مساعدتك في إدارة العملاء وتحليل التعليقات. جرب قول \"أرني عملاء الأمس\" أو \"ما هي آخر التعليقات السلبية؟\""
        : "Hello! I'm your AI assistant. I can help you manage customers and analyze feedback. Try saying 'Show me yesterday's customers' or 'What are the recent negative reviews?'",
      timestamp: new Date(),
    }
  ])
  const [inputMessage, setInputMessage] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const quickCommands = [
    {
      text: isRTL ? "أرني عملاء اليوم" : "Show me today's customers",
      icon: Users,
    },
    {
      text: isRTL ? "آخر التعليقات السلبية" : "Recent negative feedback",  
      icon: AlertTriangle,
    },
    {
      text: isRTL ? "إحصائيات هذا الأسبوع" : "This week's statistics",
      icon: TrendingUp,
    },
    {
      text: isRTL ? "أرسل رسائل متابعة" : "Send follow-up messages",
      icon: MessageSquare,
    },
  ]

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputMessage,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage("")
    setIsLoading(true)

    // Simulate AI response - in real app this would call OpenRouter API
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant", 
        content: isRTL 
          ? `تم استلام طلبك: "${inputMessage}". هذه محاكاة للرد. في النسخة الحقيقية، سأتصل بـ OpenRouter API لمعالجة طلبك وتقديم إجابات دقيقة.`
          : `I received your request: "${inputMessage}". This is a simulation. In the real version, I'll connect to OpenRouter API to process your request and provide accurate responses.`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, aiMessage])
      setIsLoading(false)
    }, 1500)
  }

  const handleQuickCommand = (command: string) => {
    setInputMessage(command)
    inputRef.current?.focus()
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const toggleVoice = () => {
    setIsListening(!isListening)
    // Voice recognition implementation would go here
  }

  return (
    <div className={`h-full flex flex-col ${isRTL ? "font-cairo" : "font-inter"}`}>
      {/* Header */}
      <div className="p-6 border-b border-slate-200">
        <div className={`flex items-center justify-between ${isRTL && "flex-row-reverse"}`}>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <Bot className="w-6 h-6 text-blue-600" />
              {t("aiAssistant")}
            </h1>
            <p className="text-slate-600 mt-1">
              {isRTL ? "اطرح أسئلتك واحصل على إجابات فورية" : "Ask questions and get instant answers"}
            </p>
          </div>
          <Button variant="outline" size="sm">
            <RefreshCw className={`w-4 h-4 ${isRTL ? "ml-1" : "mr-1"}`} />
            {isRTL ? "مسح المحادثة" : "Clear Chat"}
          </Button>
        </div>
      </div>

      {/* Quick Commands */}
      <div className="p-4 border-b border-slate-200 bg-slate-50">
        <h3 className="text-sm font-medium text-slate-700 mb-3">
          {isRTL ? "أوامر سريعة" : "Quick Commands"}
        </h3>
        <div className="flex flex-wrap gap-2">
          {quickCommands.map((command, index) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              onClick={() => handleQuickCommand(command.text)}
              className="text-xs bg-white hover:bg-blue-50 hover:border-blue-300"
            >
              <command.icon className={`w-3 h-3 ${isRTL ? "ml-1" : "mr-1"}`} />
              {command.text}
            </Button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex items-start gap-3 ${
              message.type === "user" && !isRTL ? "flex-row-reverse" : 
              message.type === "user" && isRTL ? "flex-row" : 
              isRTL ? "flex-row-reverse" : "flex-row"
            }`}
          >
            {/* Avatar */}
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              message.type === "user" ? "bg-blue-100" : "bg-green-100"
            }`}>
              {message.type === "user" ? (
                <User className="w-4 h-4 text-blue-600" />
              ) : (
                <Bot className="w-4 h-4 text-green-600" />
              )}
            </div>

            {/* Message Content */}
            <div className={`flex-1 max-w-[80%] ${
              message.type === "user" && !isRTL ? "text-right" : 
              message.type === "user" && isRTL ? "text-left" : ""
            }`}>
              <div className={`rounded-lg p-3 ${
                message.type === "user" 
                  ? "bg-blue-600 text-white ml-auto" 
                  : "bg-white border border-slate-200"
              }`}>
                <p className="text-sm">{message.content}</p>
              </div>
              <div className={`text-xs text-slate-500 mt-1 ${
                message.type === "user" && !isRTL ? "text-right" : 
                message.type === "user" && isRTL ? "text-left" : ""
              }`}>
                {message.timestamp.toLocaleTimeString(isRTL ? "ar-SA" : "en-US", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className={`flex items-start gap-3 ${isRTL ? "flex-row-reverse" : "flex-row"}`}>
            <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
              <Bot className="w-4 h-4 text-green-600" />
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{animationDelay: "0.1s"}}></div>
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{animationDelay: "0.2s"}}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-200 bg-white">
        <div className={`flex items-center gap-2 ${isRTL && "flex-row-reverse"}`}>
          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              placeholder={t("askAI")}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              className={`${isRTL ? "pr-12" : "pl-4 pr-12"}`}
              isRTL={isRTL}
            />
            <Button
              size="sm"
              variant="ghost"
              onClick={toggleVoice}
              className={`absolute top-1/2 -translate-y-1/2 ${isRTL ? "left-2" : "right-2"} ${
                isListening ? "text-red-500" : "text-slate-400"
              }`}
            >
              {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </Button>
          </div>
          <Button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="text-xs text-slate-500 mt-2 text-center">
          {isRTL 
            ? "يدعم الأوامر الصوتية باللغتين العربية والإنجليزية"
            : "Supports voice commands in Arabic and English"
          }
        </div>
      </div>
    </div>
  )
}