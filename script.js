// Current search keyword
let currentKeyword = '';

// DOM elements
const pages = document.querySelectorAll('.page');
const navLinks = document.querySelectorAll('.nav-link');
const searchForm = document.getElementById('search-form');
const searchInput = document.getElementById('search-input');
const corpusStats = document.getElementById('corpus-stats');
const currentKeywordEl = document.getElementById('current-keyword');
const frequencyCount = document.getElementById('frequency-count');
const topWordsList = document.getElementById('top-words-list');
const viewContextBtn = document.getElementById('view-context-btn');
const contextKeywordEl = document.getElementById('context-keyword');
const contextExamples = document.getElementById('context-examples');
const backToFrequencyBtn = document.getElementById('back-to-frequency');

// Upload elements
const uploadForm = document.getElementById('upload-form');
const uploadStatus = document.getElementById('upload-status');

// Document viewing elements
const documentNavLink = document.getElementById('document-nav-link');
const backToContextBtn = document.getElementById('back-to-context');
const documentTitleEl = document.getElementById('document-title');
const documentGenreEl = document.getElementById('document-genre');
const documentSourceEl = document.getElementById('document-source');
const documentContentEl = document.getElementById('document-content');

// Current document ID being viewed
let currentDocumentId = null;

// Backend API base URL
const API_URL = "http://127.0.0.1:8000";

// Initialize the app
function init() {
    searchForm.addEventListener('submit', handleSearch);
    navLinks.forEach(link => link.addEventListener('click', handleNavClick));
    viewContextBtn.addEventListener('click', () => showPage('context'));
    backToFrequencyBtn.addEventListener('click', () => showPage('frequency'));
    backToContextBtn.addEventListener('click', () => showPage('context'));
    uploadForm.addEventListener('submit', handleUpload);
    
    // Add click listener for document nav link
    documentNavLink.addEventListener('click', handleNavClick);
    
    updateCorpusStats();
}

// Fetch corpus statistics from backend
async function updateCorpusStats() {
    try {
        const res = await fetch(`${API_URL}/documents/`);
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        const docs = await res.json();

        // Check if we got an error response
        if (docs.error) {
            console.error("Server error:", docs.error);
            corpusStats.innerHTML = `<li>Error loading statistics: ${docs.error}</li>`;
            return;
        }

        const newsCount = docs.filter(doc => doc.genre === 'news').length;
        const litCount = docs.filter(doc => doc.genre === 'literature').length;
        const convCount = docs.filter(doc => doc.genre === 'conversation').length;
        const otherCount = docs.filter(doc => !doc.genre || doc.genre === 'other').length;

        corpusStats.innerHTML = `
            <li>Izindatshana zezindaba (${newsCount})</li>
            <li>Izincwadi (${litCount})</li>
            <li>Izingxoxo (${convCount})</li>
            <li>Okunye (${otherCount})</li>
            <li><strong>Isamba: ${docs.length}</strong></li>
        `;
    } catch (error) {
        console.error("Error fetching corpus stats:", error);
        corpusStats.innerHTML = `<li>Error loading statistics: ${error.message}</li>`;
    }
}

// Handle search form submission
async function handleSearch(e) {
    e.preventDefault();
    currentKeyword = searchInput.value.trim();
    
    if (currentKeyword) {
        try {
            const res = await fetch(`${API_URL}/search/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ keyword: currentKeyword })
            });
            
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            
            const data = await res.json();
            
            // Check for error response
            if (data.error) {
                console.error("Search error:", data.error);
                alert(`Search error: ${data.error}`);
                return;
            }

            frequencyCount.textContent = data.frequency;
            currentKeywordEl.textContent = data.keyword;

            await updateTopWords();
            showPage('frequency');
        } catch (error) {
            console.error("Error during search:", error);
            alert(`Search failed: ${error.message}`);
        }
    }
}

// Handle file upload
async function handleUpload(e) {
    e.preventDefault();
    
    const title = document.getElementById('document-title').value;
    const genre = document.getElementById('document-genre').value;
    const source = document.getElementById('document-source').value;
    const fileInput = document.getElementById('document-file');
    const file = fileInput.files[0];
    
    if (!file) {
        showUploadStatus('Sicela ukhethe ifayela', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('title', title);
    formData.append('genre', genre);
    formData.append('source', source);
    formData.append('file', file);
    
    try {
        showUploadStatus('Iyalayisha...', '');
        
        const res = await fetch(`${API_URL}/upload/`, {
            method: 'POST',
            body: formData
        });
        
        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.detail || `HTTP error! status: ${res.status}`);
        }
        
        const data = await res.json();
        showUploadStatus(`Incwadi "${data.title}" ilayishwe ngempumelelo!`, 'success');
        uploadForm.reset();
        
        // Update corpus stats after successful upload
        updateCorpusStats();
        
    } catch (error) {
        console.error('Upload error:', error);
        showUploadStatus(`Iphutha ekulayisheni: ${error.message}`, 'error');
    }
}

// Show upload status message
function showUploadStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = 'status-message';
    if (type === 'success') {
        uploadStatus.classList.add('status-success');
    } else if (type === 'error') {
        uploadStatus.classList.add('status-error');
    }
}

// Handle navigation clicks
function handleNavClick(e) {
    e.preventDefault();
    const page = e.target.dataset.page;
    showPage(page);
}

// Show the specified page and hide others
function showPage(pageName) {
    pages.forEach(page => {
        if (page.id === `${pageName}-page`) {
            page.classList.remove('hidden');
        } else {
            page.classList.add('hidden');
        }
    });

    navLinks.forEach(link => {
        if (link.dataset.page === pageName) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // Special handling for document page
    if (pageName === 'document') {
        documentNavLink.classList.remove('hidden');
        documentNavLink.classList.add('active');
    } else {
        documentNavLink.classList.add('hidden');
        documentNavLink.classList.remove('active');
    }

    if (pageName === 'context' && currentKeyword) {
        updateContextPage();
    }
}

// Top words (still computed on frontend for now)
async function updateTopWords() {
    try {
        const res = await fetch(`${API_URL}/documents/`);
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        
        const docs = await res.json();
        
        // Check for error response
        if (docs.error) {
            console.error("Error fetching documents:", docs.error);
            topWordsList.innerHTML = `<li>Error loading top words: ${docs.error}</li>`;
            return;
        }

        const wordCounts = {};
        docs.forEach(doc => {
            const words = doc.text.split(/\s+/);
            words.forEach(word => {
                const cleanWord = word.toLowerCase().replace(/[.,!?;:"'()]/g, '');
                if (cleanWord && cleanWord.length > 2) {
                    wordCounts[cleanWord] = (wordCounts[cleanWord] || 0) + 1;
                }
            });
        });

        const topWords = Object.entries(wordCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 20);

        topWordsList.innerHTML = topWords
            .map(([word, count]) => `<li>${word} (${count})</li>`)
            .join('');
    } catch (error) {
        console.error("Error fetching top words:", error);
        topWordsList.innerHTML = `<li>Error loading top words: ${error.message}</li>`;
    }
}

// Context display (now fetched from backend)
async function updateContextPage() {
    contextKeywordEl.textContent = currentKeyword;

    try {
        const res = await fetch(`${API_URL}/context/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ keyword: currentKeyword })
        });
        
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        
        const contexts = await res.json();
        
        // Check for error response
        if (contexts.error) {
            console.error("Context error:", contexts.error);
            contextExamples.innerHTML = `<p>Error loading context: ${contexts.error}</p>`;
            return;
        }

        if (contexts.length === 0) {
            contextExamples.innerHTML = '<p>Alukho ulwazi mayelana naleli gama esiqoqweni.</p>';
            return;
        }

        contextExamples.innerHTML = contexts.map(c => {
            return `
                <div class="context-card">
                    <h3>
                        <a href="#" class="document-link" data-doc-id="${c.doc_id}">
                            ${c.title} (${c.source})
                        </a>
                    </h3>
                    <p class="context-text">${c.context}</p>
                </div>
            `;
        }).join('');

        // Add click listeners to document links
        document.querySelectorAll('.document-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const docId = this.getAttribute('data-doc-id');
                if (docId) {
                    viewDocument(parseInt(docId));
                }
            });
        });
    } catch (error) {
        console.error("Error fetching context:", error);
        contextExamples.innerHTML = `<p>Error loading context: ${error.message}</p>`;
    }
}

// Function to view a document
async function viewDocument(docId) {
    currentDocumentId = docId;
    
    try {
        const res = await fetch(`${API_URL}/documents/${docId}`);
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        
        const doc = await res.json();
        
        if (doc.error) {
            console.error("Document error:", doc.error);
            alert(`Error loading document: ${doc.error}`);
            return;
        }

        // Display the document
        documentTitleEl.textContent = doc.title;
        documentGenreEl.textContent = doc.genre;
        documentSourceEl.textContent = doc.source;
        
        // Format the text with line breaks
        const formattedText = doc.text.replace(/\n/g, '<br>');
        documentContentEl.innerHTML = formattedText;

        // Show the document page
        showPage('document');
        
    } catch (error) {
        console.error("Error fetching document:", error);
        alert(`Error loading document: ${error.message}`);
    }
}

// Start app
document.addEventListener('DOMContentLoaded', init);