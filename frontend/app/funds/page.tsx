'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { fundApi, documentApi } from '@/lib/api'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { TrendingUp, TrendingDown, ArrowRight, Loader2, MessageSquare, FileText } from 'lucide-react'

export default function FundsPage() {
  const { data: funds, isLoading, error } = useQuery({
    queryKey: ['funds'],
    queryFn: () => fundApi.list()
  })

  // Calculate portfolio summary
  const portfolioSummary = funds?.reduce((acc: any, fund: any) => {
    const metrics = fund.metrics || {}
    return {
      totalPIC: (acc.totalPIC || 0) + (metrics.pic || 0),
      totalDistributions: (acc.totalDistributions || 0) + (metrics.total_distributions || 0),
      fundCount: (acc.fundCount || 0) + 1,
      avgDPI: (acc.avgDPI || 0) + (metrics.dpi || 0),
      avgIRR: (acc.avgIRR || 0) + (metrics.irr || 0),
    }
  }, {})

  if (portfolioSummary && funds) {
    portfolioSummary.avgDPI = portfolioSummary.avgDPI / funds.length
    portfolioSummary.avgIRR = portfolioSummary.avgIRR / funds.length
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading funds: {(error as Error).message}</p>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold mb-2">Fund Portfolio</h1>
          <p className="text-gray-600">
            View and analyze your fund investments
          </p>
        </div>
        <div className="flex space-x-3">
          <Link
            href="/documents"
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition flex items-center space-x-2"
          >
            <FileText className="w-4 h-4" />
            <span>Documents</span>
          </Link>
          <Link
            href="/upload"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Upload Document
          </Link>
        </div>
      </div>

      {/* Portfolio Summary */}
      {portfolioSummary && funds && funds.length > 0 && (
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <SummaryCard
            title="Total Funds"
            value={portfolioSummary.fundCount.toString()}
            subtitle="Active funds"
          />
          <SummaryCard
            title="Total PIC"
            value={formatCurrency(portfolioSummary.totalPIC)}
            subtitle="Paid-in capital"
          />
          <SummaryCard
            title="Avg DPI"
            value={portfolioSummary.avgDPI.toFixed(2) + 'x'}
            subtitle="Portfolio average"
          />
          <SummaryCard
            title="Avg IRR"
            value={formatPercentage(portfolioSummary.avgIRR)}
            subtitle="Portfolio average"
          />
        </div>
      )}

      {funds && funds.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <p className="text-gray-600 mb-4">No funds found. Upload a fund document to get started.</p>
          <Link
            href="/upload"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Upload Document
          </Link>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {funds?.map((fund: any) => (
            <FundCard key={fund.id} fund={fund} />
          ))}
        </div>
      )}
    </div>
  )
}

function SummaryCard({ title, value, subtitle }: {
  title: string
  value: string
  subtitle: string
}) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-sm font-medium text-gray-600 mb-1">{title}</h3>
      <p className="text-xl md:text-2xl font-bold text-gray-900 mb-1 break-words">{value}</p>
      <p className="text-xs text-gray-500">{subtitle}</p>
    </div>
  )
}

function FundCard({ fund }: { fund: any }) {
  const metrics = fund.metrics || {}
  const dpi = metrics.dpi || 0
  const irr = metrics.irr || 0
  const tvpi = metrics.tvpi || (dpi + (metrics.nav || 0) / (metrics.pic || 1))

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition p-6 h-full flex flex-col">
      <div className="mb-4">
        <h3 className="text-xl font-semibold text-gray-900 mb-1">
          {fund.name}
        </h3>
        {fund.gp_name && (
          <p className="text-sm text-gray-600">GP: {fund.gp_name}</p>
        )}
        {fund.vintage_year && (
          <p className="text-sm text-gray-500">Vintage: {fund.vintage_year}</p>
        )}
      </div>

      <div className="space-y-3 mb-4 flex-1">
        <MetricRow
          label="DPI"
          value={dpi.toFixed(2) + 'x'}
          positive={dpi >= 1}
        />
        <MetricRow
          label="IRR"
          value={formatPercentage(irr)}
          positive={irr >= 0}
        />
        <MetricRow
          label="TVPI"
          value={tvpi.toFixed(2) + 'x'}
          positive={tvpi >= 1}
        />
        {metrics.pic > 0 && (
          <MetricRow
            label="Paid-In Capital"
            value={formatCurrency(metrics.pic)}
          />
        )}
      </div>

      <div className="flex items-center space-x-2 pt-4 border-t">
        <Link
          href={`/funds/${fund.id}`}
          className="flex-1 flex items-center justify-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm"
        >
          <span>View Details</span>
          <ArrowRight className="w-4 h-4 ml-1" />
        </Link>
        <Link
          href={`/chat?fund=${fund.id}`}
          className="p-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
          title="Chat about this fund"
        >
          <MessageSquare className="w-4 h-4" />
        </Link>
      </div>
    </div>
  )
}

function MetricRow({ label, value, positive }: { 
  label: string
  value: string
  positive?: boolean 
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-600">{label}</span>
      <div className="flex items-center space-x-1">
        <span className="font-semibold text-gray-900">{value}</span>
        {positive !== undefined && (
          positive ? (
            <TrendingUp className="w-4 h-4 text-green-600" />
          ) : (
            <TrendingDown className="w-4 h-4 text-red-600" />
          )
        )}
      </div>
    </div>
  )
}
