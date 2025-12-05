# Frontend HTML Fix Required

## Problem
The `index.html` file is missing critical elements that JavaScript expects:
- `zone-title` - heading element for zone name
- Proper structure for records section with comment toggle and action buttons

## Required HTML Changes

Replace lines 111-131 in `index.html` with:

```html
                    <!-- Zone Records Section -->
                    <div id="records-section" class="records-section" style="display: none;">
                        <div class="section-header">
                            <h2 id="zone-title">Zone Records</h2>
                            <div class="section-actions">
                                <button id="add-record-btn" class="btn btn-primary">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" style="width: 18px; height: 18px;">
                                        <line x1="12" y1="5" x2="12" y2="19"/>
                                        <line x1="5" y1="12" x2="19" y2="12"/>
                                    </svg>
                                    Add Record
                                </button>
                                <button id="reload-zone-btn" class="btn btn-secondary">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" style="width: 18px; height: 18px;">
                                        <path d="M23 4v6h-6"/>
                                        <path d="M1 20v-6h6"/>
                                        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                                    </svg>
                                    Reload Zone
                                </button>
                            </div>
                        </div>

                        <div class="soa-section">
                            <div id="soa-info" class="soa-info"></div>
                        </div>

                        <div class="comment-toggle">
                            <label>
                                <input type="checkbox" id="show-comments-toggle" checked>
                                <span>Show Comments</span>
                            </label>
                        </div>

                        <div class="records-table-container">
                            <table id="records-table" class="records-table">
                                <thead>
                                    <tr>
                                        <th>Type</th>
                                        <th>Name</th>
                                        <th>Value</th>
                                        <th class="comment-column">Comment</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="records-tbody">
                                </tbody>
                            </table>
                        </div>
                    </div>
```

## Manual Fix Instructions

1. Open `frontend/index.html` on the server
2. Find the section starting with `<!-- Zone Records Section -->` (around line 111)
3. Replace the entire `records-section` div with the code above
4. Save and refresh your browser

This will add:
- The missing `zone-title` heading
- Add Record button
- Reload Zone button  
- Proper structure for SOA info
- Comment toggle
- Records table

After this fix, the zone records should display correctly!
