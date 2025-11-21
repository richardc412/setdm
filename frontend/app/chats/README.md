# Instagram DMs Page

This page displays a list of Instagram direct messages through the Unipile API integration.

## Features

### Current Features
- ✅ Display all Instagram DMs in a sidebar
- ✅ Sticky header that stays visible while scrolling
- ✅ Filter by unread/read status
- ✅ Real-time chat list with unread counts
- ✅ Relative timestamps (e.g., "5m ago", "2h ago")
- ✅ Pagination support (load more)
- ✅ Click to select a chat
- ✅ Responsive design with dark mode support
- ✅ Instagram-focused interface (no other platforms)

### Upcoming Features
- 📝 View chat messages
- 📝 Send messages
- 📝 Search chats
- 📝 Mark as read/unread
- 📝 Real-time updates
- 📝 Chat archiving

## File Structure

```
frontend/app/chats/
├── page.tsx          # Main chats page component
└── README.md         # This file

frontend/components/
└── ChatListItem.tsx  # Reusable chat list item component

frontend/lib/
└── api.ts            # API functions (includes getChats)
```

## API Integration

The page calls the backend endpoint `/api/unipile/chats` with `account_type=INSTAGRAM` to fetch only Instagram direct messages.

### Available Filters

```typescript
interface ChatFilters {
  unread?: boolean;      // Filter unread/read chats
  cursor?: string;       // Pagination cursor
  before?: string;       // ISO 8601 datetime
  after?: string;        // ISO 8601 datetime
  limit?: number;        // 1-250 (default: 50)
  account_type: string;  // Always set to "INSTAGRAM"
  account_id?: string;   // Comma-separated IDs
}
```

### Chat Data Model

```typescript
interface Chat {
  object: string;          // "Chat"
  id: string;             // Unique chat ID
  account_id: string;     // Account ID
  account_type: string;   // Platform type
  provider_id: string;    // Provider-specific ID
  name: string | null;    // Chat/contact name
  timestamp: string | null; // Last message time
  unread_count: number;   // Number of unread messages
  unread: boolean | null; // Has unread messages
}
```

## Usage

### Navigation

From the dashboard:
```typescript
router.push("/chats")
```

Or click the "💬 View Messages" button on the dashboard.

### Filtering Chats

**By Read Status:**
- Click "All" to show all Instagram DMs
- Click "Unread" to show only unread Instagram DMs

The page automatically filters to show only Instagram messages - no other platforms are displayed.

### Loading More Chats

When there are more chats available (cursor is present), a "Load More" button appears at the bottom of the chat list.

### Selecting a Chat

Click on any Instagram DM in the sidebar to select it. The main area will show:
- Instagram emoji (📷)
- Chat/contact name
- Unread message count
- Chat metadata (IDs)
- Placeholder for future message view

## Styling

The page follows the existing design system:
- Zinc color palette with dark mode support
- Tailwind CSS utility classes
- Consistent spacing and typography
- Smooth transitions and hover states
- Sticky header with `position: sticky` and `z-index: 50`

### Color Scheme

- **Background**: `zinc-50` / `black`
- **Cards**: `white` / `zinc-900`
- **Borders**: `zinc-200` / `zinc-800`
- **Primary**: `blue-600`
- **Text**: `zinc-900` / `white`
- **Muted**: `zinc-600` / `zinc-400`

## State Management

The page uses React hooks for state management:

```typescript
const [chats, setChats] = useState<Chat[]>([]);          // Chat list
const [loading, setLoading] = useState(true);            // Loading state
const [error, setError] = useState<string | null>(null); // Error state
const [selectedChat, setSelectedChat] = useState<Chat | null>(null); // Selected chat
const [filters, setFilters] = useState<ChatFilters>({    // Filter state
  limit: 50,
  account_type: "INSTAGRAM", // Always Instagram only
});
const [cursor, setCursor] = useState<string | null>(null); // Pagination cursor
```

## Error Handling

The page handles various error scenarios:
- Network errors
- API errors (401, 403, 500, etc.)
- Configuration errors (missing credentials)
- Empty states (no chats found)

Errors are displayed with a retry button.

## Performance Considerations

- Initial load fetches 50 chats
- Pagination allows loading more chats without overwhelming the UI
- Filters trigger new API requests (chats are not filtered client-side)
- The `useEffect` dependency array ensures filters update correctly

## Future Improvements

1. **Real-time Updates**: Add WebSocket support for live chat updates
2. **Search**: Add a search bar to filter chats by name or content
3. **Bulk Actions**: Select multiple chats for bulk operations
4. **Keyboard Navigation**: Arrow keys to navigate chat list
5. **Message View**: Display actual messages when a chat is selected
6. **Message Sending**: Compose and send messages
7. **Notifications**: Desktop notifications for new messages
8. **Cache**: Cache chats in localStorage for faster loads
9. **Optimistic Updates**: Update UI immediately before API confirmation
10. **Virtual Scrolling**: For better performance with thousands of chats

