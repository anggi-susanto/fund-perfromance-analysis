'use client'

import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import Link from 'next/link'
import { documentApi, fundApi } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { FileText, CheckCircle, XCircle, Loader2, Upload, Filter, Search, MessageSquare, Eye, AlertCircle } from 'lucide-react'

export default function DocumentsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [fundFilter, setFundFilter] = useState<number | null>(null)

  const { data: documents, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentApi.list()
  })

  const { data: funds } = useQuery({
    queryKey: ['funds'],
    queryFn: () => fundApi.list()
  })

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
        <p className="text-red-800">Error loading documents: {(error as Error).message}</p>
      </div>
    )
  }

  // Filter documents
  const filteredDocuments = documents?.filter((doc: any) => {
    // Search filter
    if (searchQuery && !doc.file_name.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false
    }
    // Status filter
    if (statusFilter !== 'all' && doc.parsing_status !== statusFilter) {
      return false
    }
    // Fund filter
    if (fundFilter && doc.fund_id !== fundFilter) {
      return false
    }
    return true
  }) || []

  // Calculate stats
  const stats = {
    total: documents?.length || 0,
    completed: documents?.filter((d: any) => d.parsing_status === 'completed').length || 0,
    processing: documents?.filter((d: any) => d.parsing_status === 'processing').length || 0,
    failed: documents?.filter((d: any) => d.parsing_status === 'failed' || d.parsing_status === 'completed_with_errors').length || 0,
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold mb-2">Documents</h1>
          <p className="text-gray-600">
            Manage uploaded fund performance reports
          </p>
        </div>
        <div className="flex space-x-3">
          <Link
            href="/funds"
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition flex items-center space-x-2"
          >
            <Eye className="w-4 h-4" />
            <span>View Funds</span>
          </Link>
          <Link
            href="/upload"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center space-x-2"
          >
            <Upload className="w-4 h-4" />
            <span>Upload New</span>
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <StatsCard title="Total Documents" value={stats.total} color="blue" />
        <StatsCard title="Completed" value={stats.completed} color="green" />
        <StatsCard title="Processing" value={stats.processing} color="yellow" />
        <StatsCard title="Failed/Errors" value={stats.failed} color="red" />
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="grid md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Status Filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none"
            >
              <option value="all">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
              <option value="completed_with_errors">With Errors</option>
            </select>
          </div>

          {/* Fund Filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={fundFilter || ''}
              onChange={(e) => setFundFilter(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none"
            >
              <option value="">All Funds</option>
              {funds?.map((fund: any) => (
                <option key={fund.id} value={fund.id}>
                  {fund.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {filteredDocuments.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">
            {documents && documents.length > 0 
              ? 'No documents match your filters.' 
              : 'No documents uploaded yet.'}
          </p>
          {(!documents || documents.length === 0) && (
            <Link
              href="/upload"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Upload Your First Document
            </Link>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Document
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fund
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Upload Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Processing
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredDocuments.map((doc: any) => {
                const fund = funds?.find((f: any) => f.id === doc.fund_id)
                return (
                  <tr key={doc.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <FileText className="w-5 h-5 text-gray-400 mr-3 flex-shrink-0" />
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {doc.file_name}
                          </p>
                          {doc.error_message && (
                            <p className="text-xs text-red-600 mt-1 truncate">
                              {doc.error_message}
                            </p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {fund ? (
                        <Link
                          href={`/funds/${fund.id}`}
                          className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          {fund.name}
                        </Link>
                      ) : (
                        <span className="text-sm text-gray-500">N/A</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(doc.upload_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <ProcessingStats
                        pageCount={doc.page_count}
                        chunkCount={doc.chunk_count}
                        processingStats={doc.processing_stats}
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={doc.parsing_status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex items-center space-x-2">
                        {doc.fund_id && doc.parsing_status === 'completed' && (
                          <Link
                            href={`/chat?fund=${doc.fund_id}`}
                            className="text-blue-600 hover:text-blue-800"
                            title="Ask questions"
                          >
                            <MessageSquare className="w-4 h-4" />
                          </Link>
                        )}
                        {doc.fund_id && (
                          <Link
                            href={`/funds/${doc.fund_id}`}
                            className="text-gray-600 hover:text-gray-800"
                            title="View fund"
                          >
                            <Eye className="w-4 h-4" />
                          </Link>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function StatsCard({ title, value, color }: {
  title: string
  value: number
  color: 'blue' | 'green' | 'yellow' | 'red'
}) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    red: 'bg-red-100 text-red-600',
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <p className="text-sm font-medium text-gray-600 mb-2">{title}</p>
      <p className={`text-3xl font-bold ${colorClasses[color]}`}>{value}</p>
    </div>
  )
}

function ProcessingStats({ pageCount, chunkCount, processingStats }: {
  pageCount?: number
  chunkCount?: number
  processingStats?: any
}) {
  if (!pageCount && !chunkCount) {
    return <span className="text-sm text-gray-400">N/A</span>
  }

  const hasErrors = processingStats?.errors && processingStats.errors.length > 0
  const errorCount = processingStats?.errors?.length || 0

  return (
    <div className="text-sm">
      <div className="flex items-center space-x-2">
        {pageCount && (
          <span className="text-gray-700">
            {pageCount} page{pageCount !== 1 ? 's' : ''}
          </span>
        )}
        {chunkCount && (
          <span className="text-gray-500">
            ({chunkCount} chunks)
          </span>
        )}
      </div>
      {hasErrors && (
        <div className="flex items-center space-x-1 mt-1 text-red-600">
          <AlertCircle className="w-3 h-3" />
          <span className="text-xs">{errorCount} error{errorCount !== 1 ? 's' : ''}</span>
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const statusConfig = {
    completed: {
      icon: <CheckCircle className="w-4 h-4" />,
      text: 'Completed',
      className: 'bg-green-100 text-green-800'
    },
    completed_with_errors: {
      icon: <AlertCircle className="w-4 h-4" />,
      text: 'With Errors',
      className: 'bg-yellow-100 text-yellow-800'
    },
    processing: {
      icon: <Loader2 className="w-4 h-4 animate-spin" />,
      text: 'Processing',
      className: 'bg-blue-100 text-blue-800'
    },
    pending: {
      icon: <Loader2 className="w-4 h-4" />,
      text: 'Pending',
      className: 'bg-yellow-100 text-yellow-800'
    },
    failed: {
      icon: <XCircle className="w-4 h-4" />,
      text: 'Failed',
      className: 'bg-red-100 text-red-800'
    }
  }

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending

  return (
    <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${config.className}`}>
      {config.icon}
      <span>{config.text}</span>
    </span>
  )
}
