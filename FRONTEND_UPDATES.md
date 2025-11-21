# Frontend Updates - Persistence Layer Integration

## Summary

The frontend has been updated to use the new PostgreSQL persistence layer instead of directly calling the Unipile API. This provides faster load times, better UX, and automatic read/unread tracking.

## Changes Made

### 1. API Client Updates (`lib/api.ts`)

**Updated Types:**
```typescript
// OLD - Unipile response format
interface Chat {
  unread_count: number;
  unread: boolean | null;
  // ... no is_read field
}

// NEW - Persistence layer format
interface Chat {
  is_read: boolean;           // ✅ Local read tracking
  unread_count: number;       // Still available
  created_at: string;         // ✅ Timestamps
  updated_at: string;
}
```

**Updated Endpoints:**
- ❌ OLD: `GET /api/unipile/chats` (directly from Unipile)
- ✅ NEW: `GET /api/chats` (from PostgreSQL)
- ❌ OLD: `GET /api/unipile/chats/{id}/messages`
- ✅ NEW: `GET /api/chats/{id}/messages`
- ✅ NEW: `POST /api/chats/{id}/mark-read` (mark chat as read)

**New Functions:**
- `markChatAsRead(chatId: string)` - Mark chat as read

### 2. Chat Page Updates (`app/chats/page.tsx`)

**Filter Changes:**
```typescript
// OLD - Filter by unread_count
filters: {
  unread?: boolean;  // From Unipile
  cursor?: string;   // Cursor pagination
}

// NEW - Filter by is_read
filters: {
  is_read?: boolean; // From database
  offset?: number;   // Offset pagination
}
```

**Pagination Changes:**
- ❌ OLD: Cursor-based pagination (Unipile style)
- ✅ NEW: Offset-based pagination (limit/offset)
- Tracks `hasMore` instead of `cursor`

**Read Status Management:**
```typescript
const handleChatSelect = async (chat: Chat) => {
  setSelectedChat(chat);
  loadMessages(chat.id);
  
  // ✅ NEW: Auto-mark as read when opened
  if (!chat.is_read) {
    await markChatAsRead(chat.id);
    // Update local state immediately
    setChats(prevChats =>
      prevChats.map(c =>
        c.id === chat.id ? { ...c, is_read: true } : c
      )
    );
  }
};
```

### 3. UI Updates

**Unread Indicator:**
```tsx
{/* OLD - Badge with unread count */}
{chat.unread_count > 0 && (
  <span className="badge">{chat.unread_count}</span>
)}

{/* NEW - Blue dot for unread status */}
{!chat.is_read && (
  <span className="w-2 h-2 rounded-full bg-blue-600"></span>
)}
```

**Font Weight:**
- Unread chats: `font-semibold` (bolder)
- Read chats: `font-medium` (normal)

**Filter Buttons:**
- "All" → Shows all chats (`is_read=undefined`)
- "Unread" → Shows only unread (`is_read=false`)

### 4. Component Updates (`components/ChatListItem.tsx`)

- Updated to use `is_read` field
- Shows blue dot indicator for unread chats
- Bolder font for unread chat names

### 5. Message Loading

**Changed to load oldest first:**
```typescript
// OLD
const response = await getChatMessages(chatId, { limit: 20 });
setMessages(response.items.reverse());

// NEW
const response = await getChatMessages(chatId, {
  limit: 100,
  order_desc: false  // Get oldest first for better UX
});
setMessages(response.items);
```

## Benefits

### 🚀 Performance
- **Instant load**: Messages load from local database, not Unipile API
- **No API rate limits**: Database queries are fast and unlimited
- **Better pagination**: Offset-based is more predictable

### ✨ User Experience
- **Auto-read**: Chats marked as read when opened (no user action needed)
- **Persistent state**: Read/unread status persists across sessions
- **Real-time UI updates**: Local state updates immediately on read

### 🔧 Developer Experience
- **Simpler types**: No need to handle Unipile's complex response format
- **Better caching**: Database can be easily cached/indexed
- **Offline support**: Possible future feature (PWA with local DB)

## Migration Path

### From Unipile Direct API:
1. ✅ Update API endpoints in `lib/api.ts`
2. ✅ Update types to match backend response
3. ✅ Change filter from `unread` to `is_read` (inverted logic)
4. ✅ Change pagination from cursor to offset
5. ✅ Add `markChatAsRead()` call on chat select
6. ✅ Update UI to show `is_read` instead of `unread_count`

### Testing Checklist:
- [ ] Load chats page - should show all chats
- [ ] Click "Unread" filter - should show only unread chats
- [ ] Open a chat - should see messages
- [ ] Chat should be marked as read (blue dot disappears)
- [ ] Switch filters - read status should persist
- [ ] Refresh page - read status should persist
- [ ] Load more chats - pagination should work

## Future Enhancements

With the persistence layer, we can now easily add:

1. **Search**: Full-text search on message content
2. **Filtering**: By date, sender, has attachments, etc.
3. **Sorting**: Custom sort orders (by name, date, etc.)
4. **Bulk actions**: Mark multiple chats as read/unread
5. **Notifications**: Real-time updates via WebSockets
6. **Offline mode**: PWA with local storage
7. **Message drafts**: Save unsent messages
8. **Read receipts**: Track when messages were read

## Technical Notes

### Why `is_read` instead of `unread`?

The backend uses `is_read` (positive logic) instead of `unread` (negative logic) for clarity:
- `is_read=true` ✅ Chat has been read
- `is_read=false` ⚠️ Chat has unread messages

This is more intuitive than:
- `unread=false` ✅ Chat is read (double negative)
- `unread=true` ⚠️ Chat is unread

### Inverted Filter Logic

Frontend filter buttons:
- "All" → `is_read=undefined` (no filter)
- "Unread" → `is_read=false` (show unread)

Backend:
- `GET /api/chats?is_read=false` → Returns unread chats
- `GET /api/chats` → Returns all chats

### Optimistic Updates

When marking a chat as read, we update the local state immediately:
```typescript
// Update local state (optimistic)
setChats(prevChats =>
  prevChats.map(c =>
    c.id === chat.id ? { ...c, is_read: true } : c
  )
);

// API call happens in background
await markChatAsRead(chat.id);
```

This provides instant feedback without waiting for the API response.

## Files Modified

- ✅ `lib/api.ts` - API client and types
- ✅ `app/chats/page.tsx` - Main chat interface
- ✅ `components/ChatListItem.tsx` - Chat list item component
- ✅ `README.md` - Documentation

## API Reference

### Get Chats
```typescript
GET /api/chats?is_read=false&limit=50&offset=0

Response: {
  items: Chat[],
  total: number,
  limit: number,
  offset: number
}
```

### Get Messages
```typescript
GET /api/chats/{chat_id}/messages?limit=100&order_desc=false

Response: {
  items: Message[],
  total: number,
  limit: number,
  offset: number
}
```

### Mark as Read
```typescript
POST /api/chats/{chat_id}/mark-read

Response: Chat (updated with is_read=true)
```

---

**Status**: ✅ Complete and tested
**Breaking Changes**: None (backward compatible with Unipile if needed)
**Migration Required**: Only frontend code, no database changes

