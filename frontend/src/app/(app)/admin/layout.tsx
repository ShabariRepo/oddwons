'use client'

import { useAuth } from '@/components/AuthProvider'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import Link from 'next/link'
import { Users, CreditCard, Brain, Activity, BarChart3, Twitter } from 'lucide-react'

const adminNavItems = [
  { href: '/admin', label: 'Dashboard', icon: BarChart3 },
  { href: '/admin/users', label: 'Users', icon: Users },
  { href: '/admin/billing', label: 'Billing', icon: CreditCard },
  { href: '/admin/content', label: 'Content', icon: Brain },
  { href: '/admin/x-bot', label: 'X Bot', icon: Twitter },
  { href: '/admin/system', label: 'System', icon: Activity },
]

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (user && !user.is_admin) {
      router.push('/dashboard')
    }
  }, [user, router])

  if (!user?.is_admin) {
    return (
      <div className="lg:ml-64 p-6">
        <div className="card text-center py-12">
          <h2 className="text-xl font-bold text-gray-900">Access Denied</h2>
          <p className="text-gray-500 mt-2">Admin access required</p>
        </div>
      </div>
    )
  }

  return (
    <div className="lg:ml-64 p-6">
      {/* Admin Header */}
      <div className="mb-6 pb-4 border-b">
        <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
        <p className="text-gray-500">Manage users, billing, and system</p>
      </div>

      {/* Admin Nav */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {adminNavItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 whitespace-nowrap"
          >
            <item.icon className="w-4 h-4" />
            {item.label}
          </Link>
        ))}
      </div>

      {children}
    </div>
  )
}
