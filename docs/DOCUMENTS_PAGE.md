# Documents Page Implementation

## Overview
The Documents page (`/documents`) provides a comprehensive interface for managing and monitoring all uploaded fund performance documents.

## Features Implemented

### 1. Statistics Dashboard
- **Total Documents**: Count of all uploaded documents
- **Completed**: Successfully processed documents
- **Processing**: Documents currently being processed
- **Failed/Errors**: Documents with processing failures or errors

### 2. Search and Filtering
- **Search**: Filter documents by filename (case-insensitive)
- **Status Filter**: Filter by parsing status
  - All Statuses
  - Completed
  - Processing
  - Pending
  - Failed
  - With Errors
- **Fund Filter**: Filter documents by associated fund

### 3. Document Table
Displays comprehensive information for each document:

#### Columns
1. **Document**
   - Filename with file icon
   - Error message (if any) displayed below filename in red

2. **Fund**
   - Clickable link to fund detail page
   - Shows "N/A" if not associated with a fund

3. **Upload Date**
   - Formatted date display
   - Uses `formatDate` utility function

4. **Processing**
   - Page count (e.g., "5 pages")
   - Chunk count (e.g., "42 chunks")
   - Error indicators with count if processing had errors

5. **Status**
   - Color-coded badge with icon:
     - **Completed** (green): Successfully processed
     - **With Errors** (yellow): Completed but with errors
     - **Processing** (blue): Currently being processed
     - **Pending** (yellow): Queued for processing
     - **Failed** (red): Processing failed

6. **Actions**
   - **Chat icon**: Quick link to chat page for the fund (only if completed)
   - **Eye icon**: Link to fund detail page

### 4. Navigation
- **View Funds**: Button to navigate to funds dashboard
- **Upload New**: Primary action button to upload documents
- Links to upload page when no documents exist

## Components

### DocumentsPage (Main Component)
- Manages state for search query, status filter, and fund filter
- Fetches documents and funds data using TanStack Query
- Calculates statistics dynamically
- Filters documents based on user input
- Renders table or empty state

### StatsCard
Displays a single statistic with color coding:
```typescript
StatsCard({ title, value, color })
// Colors: 'blue', 'green', 'yellow', 'red'
```

### ProcessingStats
Shows processing details for a document:
- Page count and chunk count
- Error indicators with count
- "N/A" for unprocessed documents

### StatusBadge
Color-coded status indicator with icon:
- Supports 5 statuses: completed, completed_with_errors, processing, pending, failed
- Animated spinner icon for processing status

## API Integration

Uses `documentApi` and `fundApi` from `lib/api.ts`:

```typescript
// Fetch all documents
documentApi.list()

// Fetch all funds (for filter dropdown and linking)
fundApi.list()
```

## Data Flow

1. **Initial Load**
   - Fetch documents and funds simultaneously
   - Calculate statistics
   - Display in table

2. **User Interaction**
   - **Search**: Filter documents by filename
   - **Status Filter**: Show only documents with selected status
   - **Fund Filter**: Show only documents for selected fund
   - **Click Fund Link**: Navigate to `/funds/{fundId}`
   - **Click Chat Icon**: Navigate to `/chat?fund={fundId}`
   - **Click View Funds**: Navigate to `/funds`
   - **Click Upload New**: Navigate to `/upload`

3. **Real-time Updates**
   - TanStack Query automatically refetches data
   - Status badges update when processing completes
   - Statistics recalculate based on filtered data

## Empty States

### No Documents Uploaded
- Large file icon
- Message: "No documents uploaded yet."
- Call-to-action button: "Upload Your First Document"

### No Matching Filters
- Large file icon
- Message: "No documents match your filters."
- User can adjust filters to see results

## Error Handling

1. **Loading State**
   - Shows spinner during data fetch

2. **Error State**
   - Red alert box with error message
   - Displays API error details

3. **Processing Errors**
   - Error message shown under filename
   - Error count indicator in Processing column
   - Yellow "With Errors" status badge

## Styling

- **Layout**: Max-width container (7xl)
- **Spacing**: Consistent mb-8 and mb-6 spacing
- **Colors**: Tailwind CSS utility classes
- **Icons**: lucide-react icons throughout
- **Responsive**: Grid adjusts for mobile (md:grid-cols-3)
- **Hover States**: Table rows highlight on hover
- **Focus States**: Inputs have blue focus ring

## Future Enhancements

1. **Pagination**: Add pagination for large document lists
2. **Sorting**: Allow sorting by date, filename, status
3. **Bulk Actions**: Select multiple documents for bulk operations
4. **Download**: Add download button for documents
5. **Delete**: Add delete functionality with confirmation
6. **Reprocess**: Allow reprocessing failed documents
7. **Preview**: Modal to preview document details
8. **Advanced Filters**: Date range, error type filtering
9. **Export**: Export document list as CSV/Excel

## Testing

### Manual Testing Checklist
- [ ] Load page with no documents
- [ ] Upload a document and verify it appears
- [ ] Test search functionality
- [ ] Test status filter (all options)
- [ ] Test fund filter
- [ ] Click fund link → verify navigates to fund detail
- [ ] Click chat icon → verify navigates to chat with fund selected
- [ ] Click "Upload New" → verify navigates to upload page
- [ ] Click "View Funds" → verify navigates to funds page
- [ ] Verify processing stats display correctly
- [ ] Verify error indicators show for failed documents
- [ ] Test with multiple documents and filters combined

### Integration Testing
Create test file: `tests/manual/test_documents_page.py`
```python
# Test document listing
# Test filtering
# Test status updates
# Test error handling
```

## Related Files

- **Frontend**
  - `/frontend/app/documents/page.tsx` - Main component
  - `/frontend/lib/api.ts` - API functions
  - `/frontend/lib/utils.ts` - Utility functions

- **Backend**
  - `/backend/app/api/endpoints/documents.py` - API endpoints
  - `/backend/app/models/document.py` - Document model
  - `/backend/app/schemas/document.py` - Document schemas

- **Documentation**
  - `/docs/API.md` - API documentation
  - `/docs/ARCHITECTURE.md` - System architecture
  - `/docs/CHAT_INTERFACE.md` - Chat page documentation
