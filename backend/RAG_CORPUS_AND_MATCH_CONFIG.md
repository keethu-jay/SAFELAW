# RAG Corpus and Match Function Config

We ran into an issue where the mini corpus RAG was returning 0.0000 for all similarity scores even though it was pulling the right paragraphs. The embeddings were valid (we checked in Supabase) so the problem was with the matching side.

We were using pgvector cosine distance (`<=>`) in the RPC. I switched to k nearest neighbor using inner product (`<#>`) instead. For normalized embeddings the inner product gives the same similarity conceptually but in practice it fixed the zero scores. No idea why the cosine path was failing but the inner product path works.

To make this flexible we split it into two env vars in `backend/.env`:

- **RAG_CORPUS**: Which corpus to use. `main` for the full corpus, `mini_paragraphs` or `mini_sentences` for the 5 paper test set.
- **RAG_MATCH_FN**: Which matching function to use. `cosine` uses the cosine distance RPC, `knn` uses the inner product RPC.

You can also use the older combined style: `RAG_CORPUS=mini_paragraphs_knn` which maps to mini_paragraphs corpus with the knn match function.

The server reads these at startup and the store picks the right table and RPC. Restart the backend after changing the env.
