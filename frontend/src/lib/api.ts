/**
 * API client for the Restaurant AI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ApiResponse<T> {
  data?: T
  error?: string
  message?: string
}

class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
    
    // Get token from localStorage if available
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token')
    }
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Network error' }))
        return { error: errorData.error || `HTTP ${response.status}` }
      }

      const data = await response.json()
      return { data }
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  }

  // Auth methods
  async login(email: string, password: string) {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    const response = await fetch(`${this.baseUrl}/api/v1/auth/jwt/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    })

    if (response.ok) {
      const data = await response.json()
      this.token = data.access_token
      localStorage.setItem('auth_token', this.token!)
      return { data }
    } else {
      const error = await response.json()
      return { error: error.detail || 'Login failed' }
    }
  }

  async register(userData: {
    email: string
    password: string
    first_name: string
    last_name: string
    role?: string
  }) {
    return this.request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    })
  }

  async logout() {
    this.token = null
    localStorage.removeItem('auth_token')
    return this.request('/api/v1/auth/jwt/logout', { method: 'POST' })
  }

  async getCurrentUser() {
    return this.request('/api/v1/auth/me')
  }

  // Dashboard methods
  async getDashboardStats() {
    // For now, return some calculated stats from customer data
    const customersResult = await this.getCustomers()
    if (customersResult.error) {
      return { error: customersResult.error }
    }

    const customers = customersResult.data || []
    const totalCustomers = customers.length
    const responded = customers.filter((c: any) => c.status === 'responded').length
    const positive = customers.filter((c: any) => c.feedback_sentiment === 'positive').length
    const pending = customers.filter((c: any) => c.status === 'pending').length

    return {
      data: {
        totalCustomers: totalCustomers.toString(),
        responseRate: totalCustomers > 0 ? `${Math.round((responded / totalCustomers) * 100)}%` : '0%',
        positiveReviews: positive.toString(),
        pendingFollowup: pending.toString(),
      }
    }
  }

  async getRecentFeedback() {
    const customersResult = await this.getCustomers()
    if (customersResult.error) {
      return { error: customersResult.error }
    }

    const customers = customersResult.data || []
    const recentFeedback = customers
      .filter((c: any) => c.feedback_text)
      .slice(0, 3)
      .map((c: any) => ({
        customer: `${c.first_name} ${c.last_name || ''}`.trim(),
        phone: c.phone_number,
        feedback: c.feedback_text,
        sentiment: c.feedback_sentiment || 'neutral',
        time: new Date(c.updated_at).toLocaleString('ar-SA')
      }))

    return { data: recentFeedback }
  }

  // Customer methods
  async getCustomers() {
    const result = await this.request('/api/v1/customers/')
    if (result.error) {
      return { error: result.error }
    }
    // Backend returns paginated response, extract the items array
    return { data: result.data?.items || [] }
  }

  async createCustomer(customerData: {
    first_name: string
    last_name?: string
    phone_number: string
    email?: string
    visit_date?: string
    preferred_language?: 'ar' | 'en'
  }) {
    // Add a default restaurant_id for testing
    const customerDataWithRestaurant = {
      ...customerData,
      restaurant_id: 'fe7d572e-0efb-46c5-9076-67ea27274268'
    }
    
    return this.request('/api/v1/customers/', {
      method: 'POST',
      body: JSON.stringify(customerDataWithRestaurant),
    })
  }

  async updateCustomer(id: string, customerData: any) {
    return this.request(`/api/v1/customers/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(customerData),
    })
  }

  async deleteCustomer(id: string) {
    return this.request(`/api/v1/customers/${id}/`, {
      method: 'DELETE',
    })
  }

  // Restaurant methods
  async getRestaurants() {
    return this.request('/api/v1/restaurants/')
  }

  async createRestaurant(restaurantData: any) {
    return this.request('/api/v1/restaurants/', {
      method: 'POST',
      body: JSON.stringify(restaurantData),
    })
  }

  // Analytics methods
  async getAnalyticsStats() {
    return this.request('/api/v1/customers/stats/summary')
  }

  async getRestaurantStats(restaurantId: string) {
    return this.request(`/api/v1/restaurants/${restaurantId}/stats`)
  }

  // Settings methods
  async getSettings() {
    // This would integrate with restaurant settings endpoint
    return this.request('/api/v1/restaurants/') // Get current restaurant settings
  }

  async updateSettings(settings: any) {
    // This would update restaurant settings
    return this.request('/api/v1/restaurants/', {
      method: 'PATCH',
      body: JSON.stringify(settings),
    })
  }

  // WhatsApp methods
  async sendTestWhatsApp(phoneNumber: string) {
    const encodedPhone = encodeURIComponent(phoneNumber)
    return this.request(`/api/v1/whatsapp/send-test?phone_number=${encodedPhone}`, {
      method: 'POST',
    })
  }

  async sendGreetingMessage(customerId: string, delayHours: number = 0) {
    return this.request(`/api/v1/whatsapp/send-greeting/${customerId}`, {
      method: 'POST',
      body: JSON.stringify({ delay_hours: delayHours }),
    })
  }

  async getSandboxInfo() {
    return this.request('/api/v1/whatsapp/sandbox-info')
  }
}

export const api = new ApiClient()
export default api