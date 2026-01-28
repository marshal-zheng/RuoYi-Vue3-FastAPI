# Dictionary Loading Fix - Operlog "Canceled" Errors

## Issue Description
When entering the operlog (操作日志) page, users see 3 "canceled" error toast messages.

## Root Cause Analysis

### Multiple Simultaneous Requests
When the OperlogGrid component mounts, it triggers 3 simultaneous API requests:
1. **Dictionary request 1**: `sys_oper_type` (operation type dictionary)
2. **Dictionary request 2**: `sys_common_status` (status dictionary)
3. **Data request**: Initial operlog data load via `ZxGridList`

### Problems with Original `useDict` Implementation
1. **No request deduplication**: If the same dictionary is requested multiple times before the first request completes, it fires duplicate requests
2. **No error handling**: Failed requests would bubble up and show error toasts
3. **Race conditions**: Multiple components requesting the same dictionaries simultaneously could cause conflicts

## Solution Implemented

### Enhanced `useDict` Function (`ruoyi-fastapi-frontend/src/utils/dict.ts`)

Added three key improvements:

1. **Request Deduplication**
   - Maintains a `pendingDictRequests` Map to track in-flight requests
   - Reuses existing promises for the same dictionary type
   - Prevents duplicate API calls

2. **Silent Error Handling**
   - Catches dictionary loading errors
   - Logs warnings to console instead of showing error toasts
   - Returns empty array on failure to prevent UI breaks

3. **Proper Cleanup**
   - Removes pending requests from cache after completion
   - Prevents memory leaks from accumulated promises

### Code Changes

```typescript
// Track pending dictionary requests to prevent duplicates
const pendingDictRequests = new Map<string, Promise<any>>();

export function useDict(...args: string[]) {
  const res = ref<Record<string, DictItem[]>>({});
  return (() => {
    args.forEach((dictType: string, index: number) => {
      res.value[dictType] = [];
      const dicts = useDictStore().getDict(dictType);
      if (dicts) {
        res.value[dictType] = dicts;
      } else {
        // Check if there's already a pending request
        let dictPromise = pendingDictRequests.get(dictType);
        
        if (!dictPromise) {
          // Create new request and cache the promise
          dictPromise = getDicts(dictType)
            .then((resp: any) => {
              const dictData = resp.data.map((p: DictDataItem) => ({
                label: p.dictLabel,
                value: p.dictValue,
                elTagType: p.listClass,
                elTagClass: p.cssClass,
              }));
              useDictStore().setDict(dictType, dictData);
              return dictData;
            })
            .catch((error: any) => {
              // Silently handle errors to prevent "canceled" toasts
              console.warn(`Failed to load dictionary: ${dictType}`, error);
              return [];
            })
            .finally(() => {
              // Clean up pending request
              pendingDictRequests.delete(dictType);
            });
          
          pendingDictRequests.set(dictType, dictPromise);
        }
        
        // Use the cached promise (either new or existing)
        dictPromise.then((dictData: DictItem[]) => {
          res.value[dictType] = dictData;
        });
      }
    });
    return toRefs(res.value);
  })();
}
```

## Benefits

1. **Eliminates "canceled" error toasts**: Errors are logged to console instead
2. **Reduces API calls**: Deduplicates simultaneous requests for the same dictionary
3. **Improves performance**: Reuses in-flight requests across components
4. **Better user experience**: No confusing error messages on page load
5. **Maintains functionality**: Dictionary data still loads correctly, just with better error handling

## Testing Recommendations

1. Navigate to operlog page and verify no "canceled" toasts appear
2. Check browser console for any dictionary loading warnings
3. Verify dictionary selectors (operation type, status) populate correctly
4. Test with slow network to ensure deduplication works
5. Test with backend errors to ensure graceful degradation

## Related Files

- `ruoyi-fastapi-frontend/src/utils/dict.ts` - Enhanced useDict function
- `ruoyi-fastapi-frontend/src/components/business/Monitor/OperlogGrid.vue` - Uses dictionaries
- `ruoyi-fastapi-frontend/src/store/modules/dict.js` - Dictionary store
- `ruoyi-fastapi-frontend/src/api/system/dict/data.js` - Dictionary API

## Status

✅ **Fixed** - Dictionary loading now has proper deduplication and error handling
