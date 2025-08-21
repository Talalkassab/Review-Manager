'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface Restaurant {
  id: string;
  name: string;
  name_arabic?: string;
  description?: string;
  logo_url?: string;
  persona?: string;
  phone_number?: string;
  email?: string;
  city?: string;
  is_active: boolean;
}

export default function RestaurantsPage() {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    name_arabic: '',
    description: '',
    logo_url: '',
    persona: '',
    phone_number: '',
    email: '',
    city: '',
    address: '',
  });

  useEffect(() => {
    fetchRestaurants();
  }, []);

  const fetchRestaurants = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/restaurants', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setRestaurants(data);
      }
    } catch (error) {
      console.error('Error fetching restaurants:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8000/api/v1/restaurants', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setIsCreating(false);
        setFormData({
          name: '',
          name_arabic: '',
          description: '',
          logo_url: '',
          persona: '',
          phone_number: '',
          email: '',
          city: '',
          address: '',
        });
        fetchRestaurants();
      }
    } catch (error) {
      console.error('Error creating restaurant:', error);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Restaurants</h1>
        <Button onClick={() => setIsCreating(true)}>Create Restaurant</Button>
      </div>

      {isCreating && (
        <Card className="p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Create New Restaurant</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Restaurant Name *</Label>
                <Input
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                />
              </div>
              <div>
                <Label htmlFor="name_arabic">Restaurant Name (Arabic)</Label>
                <Input
                  id="name_arabic"
                  name="name_arabic"
                  value={formData.name_arabic}
                  onChange={handleInputChange}
                  dir="rtl"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border rounded-md"
                rows={3}
              />
            </div>

            <div>
              <Label htmlFor="logo_url">Logo URL</Label>
              <Input
                id="logo_url"
                name="logo_url"
                type="url"
                value={formData.logo_url}
                onChange={handleInputChange}
                placeholder="https://example.com/logo.png"
              />
              {formData.logo_url && (
                <img
                  src={formData.logo_url}
                  alt="Logo preview"
                  className="mt-2 h-20 w-20 object-contain"
                />
              )}
            </div>

            <div>
              <Label htmlFor="persona">Communication Persona</Label>
              <textarea
                id="persona"
                name="persona"
                value={formData.persona}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border rounded-md"
                rows={3}
                placeholder="e.g., Friendly and welcoming, professional yet approachable..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="phone_number">Phone Number</Label>
                <Input
                  id="phone_number"
                  name="phone_number"
                  value={formData.phone_number}
                  onChange={handleInputChange}
                />
              </div>
              <div>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleInputChange}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="city">City</Label>
                <Input
                  id="city"
                  name="city"
                  value={formData.city}
                  onChange={handleInputChange}
                />
              </div>
              <div>
                <Label htmlFor="address">Address</Label>
                <Input
                  id="address"
                  name="address"
                  value={formData.address}
                  onChange={handleInputChange}
                />
              </div>
            </div>

            <div className="flex gap-4">
              <Button type="submit">Create Restaurant</Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsCreating(false)}
              >
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {restaurants.map((restaurant) => (
          <Card key={restaurant.id} className="p-6">
            {restaurant.logo_url && (
              <img
                src={restaurant.logo_url}
                alt={restaurant.name}
                className="h-16 w-16 object-contain mb-4"
              />
            )}
            <h3 className="text-lg font-semibold">{restaurant.name}</h3>
            {restaurant.name_arabic && (
              <p className="text-gray-600" dir="rtl">{restaurant.name_arabic}</p>
            )}
            {restaurant.description && (
              <p className="text-sm text-gray-600 mt-2">{restaurant.description}</p>
            )}
            {restaurant.persona && (
              <p className="text-sm text-blue-600 mt-2">Persona: {restaurant.persona}</p>
            )}
            <div className="mt-4 text-sm text-gray-500">
              {restaurant.city && <p>City: {restaurant.city}</p>}
              {restaurant.phone_number && <p>Phone: {restaurant.phone_number}</p>}
              {restaurant.email && <p>Email: {restaurant.email}</p>}
            </div>
            <div className="mt-4">
              <span className={`px-2 py-1 text-xs rounded ${
                restaurant.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {restaurant.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}