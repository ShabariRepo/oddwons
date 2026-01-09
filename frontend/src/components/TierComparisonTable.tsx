'use client'

import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import Image from 'next/image'
import { clsx } from 'clsx'

const features = [
  { name: 'Summary', free: true, basic: true, premium: true, pro: true },
  { name: 'Implied probability', free: true, basic: true, premium: true, pro: true },
  { name: 'Current odds (Yes/No)', free: true, basic: true, premium: true, pro: true },
  { name: 'Volume note', free: false, basic: true, premium: true, pro: true },
  { name: 'Recent movement %', free: false, basic: true, premium: true, pro: true },
  { name: 'Movement context ("Why It Moved")', free: false, basic: false, premium: true, pro: true },
  { name: 'Upcoming catalyst', free: false, basic: false, premium: true, pro: true },
  { name: 'Source articles (our homework)', free: false, basic: false, premium: true, pro: true },
  { name: 'Analyst note (full AI analysis)', free: false, basic: false, premium: false, pro: true },
]

interface TierComparisonTableProps {
  defaultOpen?: boolean
  className?: string
}

export default function TierComparisonTable({ defaultOpen = false, className }: TierComparisonTableProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className={clsx('w-full', className)}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-gray-700 font-medium"
      >
        <span>Compare All Features</span>
        <ChevronDown
          className={clsx(
            'w-5 h-5 transition-transform duration-300',
            isOpen && 'rotate-180'
          )}
        />
      </button>

      {/* Expandable Content */}
      <div
        className={clsx(
          'overflow-hidden transition-all duration-500 ease-in-out',
          isOpen ? 'max-h-[800px] opacity-100 mt-4' : 'max-h-0 opacity-0'
        )}
      >
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                    Feature
                  </th>
                  <th className="px-4 py-3 text-center text-sm font-semibold text-gray-500">
                    Free
                  </th>
                  <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900">
                    Basic
                  </th>
                  <th className="px-4 py-3 text-center text-sm font-semibold text-primary-600">
                    Premium
                  </th>
                  <th className="px-4 py-3 text-center text-sm font-semibold text-amber-600">
                    Pro
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {features.map((feature, idx) => (
                  <tr
                    key={feature.name}
                    className={clsx(
                      'transition-colors hover:bg-gray-50',
                      idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'
                    )}
                  >
                    <td className="px-4 py-3 text-sm text-gray-700">
                      {feature.name}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {feature.free ? (
                        <Image
                          src="/oddwons-logo.png"
                          alt="Included"
                          width={20}
                          height={20}
                          className="inline-block opacity-80"
                        />
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {feature.basic ? (
                        <Image
                          src="/oddwons-logo.png"
                          alt="Included"
                          width={20}
                          height={20}
                          className="inline-block"
                        />
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center bg-primary-50/30">
                      {feature.premium ? (
                        <Image
                          src="/oddwons-logo.png"
                          alt="Included"
                          width={20}
                          height={20}
                          className="inline-block"
                        />
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center bg-amber-50/30">
                      {feature.pro ? (
                        <Image
                          src="/oddwons-logo.png"
                          alt="Included"
                          width={20}
                          height={20}
                          className="inline-block"
                        />
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
