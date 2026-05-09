/**
 * useSheetTopoSort
 *
 * Frontend topological sort for target sheets, aligned with the backend
 * `topo_sort_sheets` in `apps/processing/services.py`.
 *
 * Shared rules (Requirements 5.1 / 5.3 / 5.4):
 *  - Self-loops (upstream === downstream) are silently ignored.
 *  - Edges referencing a sheet_name that is not present in `nodes` are ignored.
 *  - Zero-indegree nodes are popped from a min-heap keyed by
 *    `(sort_order, sheet_name)` — this guarantees idempotent output for
 *    identical input, matching the backend contract.
 *  - On cycle: returns the fallback order (ascending `(sort_order, sheet_name)`)
 *    with `cycle = true`, so the UI can surface a circular-dependency banner.
 *
 * Pure function — depends on zero Vue APIs — so it is trivially unit-testable
 * via Vitest / fast-check.
 */

export interface SheetNode {
  sheet_name: string
  sort_order: number
}

export interface LineageEdge {
  upstream: string
  downstream: string
}

export interface TopoResult {
  /** Sheet names in execution order (length === nodes.length). */
  order: string[]
  /** True when the input edges form a cycle (after self-loop/unknown filtering). */
  cycle: boolean
}

// ---------------------------------------------------------------------------
// Minimal binary min-heap keyed by (sort_order, sheet_name).
// Kept local so the composable remains dependency-free.
// ---------------------------------------------------------------------------

type HeapEntry = { sortOrder: number; name: string }

function heapLess(a: HeapEntry, b: HeapEntry): boolean {
  if (a.sortOrder !== b.sortOrder) return a.sortOrder < b.sortOrder
  return a.name < b.name
}

function heapPush(heap: HeapEntry[], item: HeapEntry): void {
  heap.push(item)
  let i = heap.length - 1
  while (i > 0) {
    const parent = (i - 1) >> 1
    const cur = heap[i] as HeapEntry
    const par = heap[parent] as HeapEntry
    if (heapLess(cur, par)) {
      heap[i] = par
      heap[parent] = cur
      i = parent
    } else {
      break
    }
  }
}

function heapPop(heap: HeapEntry[]): HeapEntry | undefined {
  const n = heap.length
  if (n === 0) return undefined
  const top = heap[0] as HeapEntry
  const last = heap.pop() as HeapEntry
  if (n > 1) {
    heap[0] = last
    let i = 0
    const size = heap.length
    while (true) {
      const l = i * 2 + 1
      const r = i * 2 + 2
      let smallest = i
      if (l < size && heapLess(heap[l] as HeapEntry, heap[smallest] as HeapEntry)) smallest = l
      if (r < size && heapLess(heap[r] as HeapEntry, heap[smallest] as HeapEntry)) smallest = r
      if (smallest === i) break
      const a = heap[i] as HeapEntry
      const b = heap[smallest] as HeapEntry
      heap[i] = b
      heap[smallest] = a
      i = smallest
    }
  }
  return top
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export function topoSortSheets<T extends SheetNode>(
  nodes: T[],
  edges: LineageEdge[],
): TopoResult {
  const nameSet = new Set<string>()
  const sortOrderByName = new Map<string, number>()
  for (const n of nodes) {
    if (!n || typeof n.sheet_name !== 'string' || !n.sheet_name) continue
    if (nameSet.has(n.sheet_name)) continue
    nameSet.add(n.sheet_name)
    sortOrderByName.set(n.sheet_name, Number(n.sort_order ?? 0))
  }

  const graph = new Map<string, string[]>()
  const indeg = new Map<string, number>()
  for (const name of nameSet) {
    graph.set(name, [])
    indeg.set(name, 0)
  }

  for (const e of edges || []) {
    if (!e) continue
    const up = e.upstream
    const down = e.downstream
    if (!nameSet.has(up) || !nameSet.has(down)) continue
    if (up === down) continue // ignore self-loop
    graph.get(up)!.push(down)
    indeg.set(down, (indeg.get(down) || 0) + 1)
  }

  const heap: HeapEntry[] = []
  for (const name of nameSet) {
    if ((indeg.get(name) || 0) === 0) {
      heapPush(heap, { sortOrder: sortOrderByName.get(name) || 0, name })
    }
  }

  const order: string[] = []
  while (heap.length > 0) {
    const top = heapPop(heap)!
    order.push(top.name)
    for (const nxt of graph.get(top.name) || []) {
      indeg.set(nxt, (indeg.get(nxt) || 0) - 1)
      if ((indeg.get(nxt) || 0) === 0) {
        heapPush(heap, { sortOrder: sortOrderByName.get(nxt) || 0, name: nxt })
      }
    }
  }

  if (order.length !== nameSet.size) {
    // Fallback: stable order by (sort_order, sheet_name) ascending
    const fallback = Array.from(nameSet).sort((a, b) => {
      const soA = sortOrderByName.get(a) || 0
      const soB = sortOrderByName.get(b) || 0
      if (soA !== soB) return soA - soB
      return a < b ? -1 : a > b ? 1 : 0
    })
    return { order: fallback, cycle: true }
  }

  return { order, cycle: false }
}
