# Why Tab Sometimes Shows No Suggestions (0) Then Fills on Retry

When you press Tab in the Corpus Studio tool and sometimes get no suggestions or a similarity score of 0, but on a second or third Tab the values appear correctly (in decreasing order), the cause is usually one of these:

1. **Cold start / first request**  
   The first request after the app has been idle may hit a server that is still waking up or a cold embedding/DB path. That request can time out or return an empty/error response, so the UI shows nothing or 0. A second Tab triggers a new request that completes successfully, so you then see the full list in decreasing order.

2. **Timeout**  
   Embedding the query and running the vector search can take a few seconds. If the frontend or gateway has a short timeout (e.g. 5 seconds), the first request might be cut off before the backend responds. The UI then shows blank or 0. A later Tab might complete within the timeout and display the correct suggestions.

3. **Race / debouncing**  
   If the UI sends a request on each Tab and updates state when the response arrives, a second Tab before the first response can cause the first response to be ignored or overwritten. That can look like “first Tab does nothing, second Tab works” (or the opposite), depending on timing.

4. **Backend or DB briefly unavailable**  
   A single failed or empty response (e.g. Supabase or the embedding API briefly failing) leads to 0 or no suggestions. The next Tab triggers a new request that succeeds, so values then appear in the correct order.

So the behavior is consistent with **transient failures or timing (cold start, timeout, race)** rather than a bug in the ordering logic. The script/notebook below avoids this by calling the retrieval logic once per test paragraph and only recording the top 10 suggestions and their semantic scores when **all 10 values are non-blank**, so you don’t get partial or “first Tab empty” rows in your analysis.
