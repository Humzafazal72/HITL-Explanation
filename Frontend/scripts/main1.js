// Configuration
const API_BASE_URL = 'http://localhost:8000'; // Update this to your actual API URL

// State management
let currentConceptId = null;
let currentConceptName = null;
let figureChangeDescriptions = {};
let figuresToDelete = new Set();

// Screen management
const screens = {
    initial: document.getElementById('initialScreen'),
    loading: document.getElementById('loadingScreen'),
    explanationReview: document.getElementById('explanationReviewScreen'),
    figureReview: document.getElementById('figureReviewScreen'),
    finalReview: document.getElementById('finalReviewScreen'),
    success: document.getElementById('successScreen')
};

// Initialize event listeners
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
});

function initializeEventListeners() {
    // Concept form submission
    document.getElementById('generateBtn').addEventListener('click', handleConceptSubmit);

    // Explanation review checkbox
    document.getElementById('explanationChangeCheckbox').addEventListener('change', (e) => {
        const commentBox = document.getElementById('explanationCommentBox');
        if (e.target.checked) {
            commentBox.classList.remove('hidden');
        } else {
            commentBox.classList.add('hidden');
            document.getElementById('explanationComment').value = '';
        }
    });

    // Submit explanation review
    document.getElementById('submitExplanationReview').addEventListener('click', handleExplanationReviewSubmit);

    // Submit figure review
    document.getElementById('submitFigureReview').addEventListener('click', handleFigureReviewSubmit);

    // Upload to cloud
    document.getElementById('uploadToCloud').addEventListener('click', handleUploadToCloud);

    // Start over and create another
    document.getElementById('startOver').addEventListener('click', resetToInitial);
    document.getElementById('createAnother').addEventListener('click', resetToInitial);
}

// Handle concept form submission
async function handleConceptSubmit(e) {
    e.preventDefault();
    const conceptInput = document.getElementById('conceptInput');
    currentConceptName = conceptInput.value.trim();
    
    if (!currentConceptName) {
        showError('Please enter a concept name');
        return;
    }

    showScreen('loading');
    setLoadingMessage('Generating explanation...');

    try {
        await startAgentHITL(currentConceptName);
    } catch (error) {
        console.error('Error starting agent:', error);
        showError('Failed to start explanation generation. Please try again.');
        showScreen('initial');
    }
}

// Start the agent HITL process
function startAgentHITL(concept) {
    return new Promise((resolve, reject) => {
        const url = `${API_BASE_URL}/hitl/start_agent_hitl?concept=${encodeURIComponent(concept)}`;
        
        console.log('Starting agent with URL:', url);

        fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'text/event-stream',
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            console.log('Fetch response received, starting stream...');
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let currentEvent = {};

            function readStream() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        console.log('Stream ended');
                        resolve();
                        return;
                    }

                    try {
                        buffer += decoder.decode(value, { stream: true });
                        const lines = buffer.split('\n');
                        
                        // Keep the last incomplete line in the buffer
                        buffer = lines.pop() || '';

                        lines.forEach(line => {
                            line = line.trim();
                            
                            if (line.startsWith('event:')) {
                                currentEvent.event = line.slice(6).trim();
                                console.log('Event type:', currentEvent.event);
                            } else if (line.startsWith('id:')) {
                                currentEvent.id = line.slice(3).trim();
                                if (currentEvent.id) {
                                    currentConceptId = currentEvent.id;
                                }
                            } else if (line.startsWith('data:')) {
                                currentEvent.data = line.slice(5).trim();
                            } else if (line === '') {
                                // Empty line means end of event, process it
                                if (currentEvent.event && currentEvent.data) {
                                    try {
                                        const parsedData = JSON.parse(currentEvent.data);
                                        console.log('Parsed event data:', parsedData);
                                        
                                        // Call handleSSEEvent but don't await to prevent blocking the stream
                                        handleSSEEvent(currentEvent.event, parsedData).catch(err => {
                                            console.error('Error in handleSSEEvent:', err);
                                        });
                                    } catch (error) {
                                        console.error('Error parsing event data:', error, currentEvent.data);
                                    }
                                }
                                currentEvent = {};
                            }
                        });

                        // Continue reading
                        readStream();
                    } catch (error) {
                        console.error('Error processing stream chunk:', error);
                        // Continue reading even if there's an error processing
                        readStream();
                    }
                }).catch(error => {
                    console.error('Stream read error:', error);
                    // Only reject if it's a real connection error
                    if (error.name !== 'AbortError') {
                        reject(error);
                    }
                });
            }

            readStream();
        })
        .catch(error => {
            console.error('Fetch error:', error);
            reject(error);
        });
    });
}

// Add this at the top with other state management
let lastNodeExecuted = null;
let workflowEnded = false;

// Modified handleSSEEvent function
async function handleSSEEvent(eventName, data) {
    console.log('=== handleSSEEvent START ===');
    console.log('Event name:', eventName);
    console.log('Event data:', data);
    console.log('Current screen:', Object.keys(screens).find(key => screens[key].classList.contains('active')));

    try {
        if (eventName === '__interrupt__') {
            console.log('Interrupt received:', data);
            
            if (data.type === 'explanation') {
                console.log('Loading explanation review (no figures)...');
                await loadAndShowExplanation(false);
                console.log('Explanation review loaded');
            } else if (data.type === 'figure') {
                console.log('Loading figure review...');
                await loadAndShowExplanation(true);
                console.log('Figure review loaded');
            }
        } else {
            // Regular node execution
            console.log(`Regular node executed: ${eventName}`);
            lastNodeExecuted = eventName;
            
            // Check if this is an empty data signal (indicates workflow continuation/end)
            if (data && Object.keys(data).length === 1 && data[""] === "") {
                console.log('Empty data received for node:', eventName);
                
                // If we just executed fig_reviewer and got empty data, workflow is complete
                if (eventName === 'fig_reviewer') {
                    console.log('Workflow completed after fig_reviewer, showing final review');
                    workflowEnded = true;
                    await showFinalReview();
                }
            }
        }
    } catch (error) {
        console.error('ERROR in handleSSEEvent:', error);
        console.error('Error stack:', error.stack);
        // Don't rethrow - we don't want to break the SSE stream
    }
    
    console.log('=== handleSSEEvent END ===');
}

// Handle SSE messages (legacy format for resume endpoint)
async function handleSSEMessage(data) {
    console.log('SSE Message:', data);

    // Check if this is interrupt data (has 'type' and 'prompt' fields)
    if (data.type === 'explanation') {
        console.log('Explanation interrupt received');
        await loadAndShowExplanation(false);
    } else if (data.type === 'figure') {
        console.log('Figure interrupt received');
        await loadAndShowExplanation(true);
    } else if (data[""] === "") {
        // Empty data object - node execution
        console.log('Node executed (empty data)');
    } else {
        console.log('Other data received:', data);
    }
}

// Load and display explanation
async function loadAndShowExplanation(includeFigures) {
    console.log('loadAndShowExplanation called with includeFigures:', includeFigures);
    try {
        setLoadingMessage('Loading explanation...');
        const explanationData = await fetchExplanationData(includeFigures);
        console.log('Explanation data fetched successfully');
        
        if (includeFigures) {
            displayFigureReview(explanationData);
        } else {
            displayExplanationReview(explanationData);
        }
    } catch (error) {
        console.error('Error loading explanation:', error);
        console.error('Error details:', error.message, error.stack);
        showError('Failed to load explanation: ' + error.message);
        // DON'T reset to initial screen - this might be called during stream processing
        // showScreen('initial');
    }
}

// Fetch explanation data from API
async function fetchExplanationData(includeDiagrams) {
    const url = `${API_BASE_URL}/crud/get_data/?concept_id=${currentConceptId}&diagrams=${includeDiagrams}`;
    const response = await fetch(url);
    
    if (!response.ok) {
        throw new Error('Failed to fetch explanation data');
    }
    
    return await response.json();
}

// Display explanation review screen
function displayExplanationReview(data) {
    document.getElementById('contextText').textContent = data.context;
    document.getElementById('conclusionText').textContent = data.conclusion;

    const stepsContainer = document.getElementById('stepsContainer');
    stepsContainer.innerHTML = '';

    data.steps.forEach((step, index) => {
        const stepDiv = document.createElement('div');
        stepDiv.className = 'step-item';
        stepDiv.innerHTML = `<div class="step-text">${step.text}</div>`;
        stepsContainer.appendChild(stepDiv);
    });

    // Reset form
    document.getElementById('explanationChangeCheckbox').checked = false;
    document.getElementById('explanationCommentBox').classList.add('hidden');
    document.getElementById('explanationComment').value = '';

    showScreen('explanationReview');
}

// Display figure review screen
function displayFigureReview(data) {
    // Reset tracking objects
    figureChangeDescriptions = {};
    figuresToDelete = new Set();

    document.getElementById('figureContextText').textContent = data.context;
    document.getElementById('figureConclusionText').textContent = data.conclusion;

    const stepsContainer = document.getElementById('figureStepsContainer');
    stepsContainer.innerHTML = '';

    data.steps.forEach((step, index) => {
        const stepDiv = document.createElement('div');
        stepDiv.className = 'step-item';
        
        let stepHTML = `<div class="step-text">${step.text}</div>`;
        
        if (step.figure) {
            const figureId = `fig_${index}`;
            stepHTML += `
                <div class="figure-container" id="figure-container-${index}">
                    <img src="data:image/png;base64,${step.figure}" alt="Figure ${index}">
                    <div class="figure-actions">
                        <div class="figure-action-group">
                            <div class="checkbox-group">
                                <input type="checkbox" id="comment-checkbox-${index}" data-figure="${figureId}">
                                <label for="comment-checkbox-${index}">Add improvement comment</label>
                            </div>
                            <textarea 
                                class="figure-comment hidden" 
                                id="comment-${index}" 
                                data-figure="${figureId}"
                                placeholder="Describe improvements for this figure..."
                                rows="3"
                            ></textarea>
                        </div>
                        <button class="delete-button" id="delete-${index}" data-figure="${figureId}">
                            Delete Figure
                        </button>
                    </div>
                </div>
            `;
        }
        
        stepDiv.innerHTML = stepHTML;
        stepsContainer.appendChild(stepDiv);

        // Add event listeners for this figure
        if (step.figure) {
            const figureId = `fig_${index}`;
            
            // Comment checkbox listener
            const commentCheckbox = document.getElementById(`comment-checkbox-${index}`);
            commentCheckbox.addEventListener('change', (e) => {
                const commentBox = document.getElementById(`comment-${index}`);
                if (e.target.checked) {
                    commentBox.classList.remove('hidden');
                } else {
                    commentBox.classList.add('hidden');
                    commentBox.value = '';
                    delete figureChangeDescriptions[figureId];
                }
            });

            // Comment textarea listener
            const commentTextarea = document.getElementById(`comment-${index}`);
            commentTextarea.addEventListener('input', (e) => {
                if (e.target.value.trim()) {
                    figureChangeDescriptions[figureId] = e.target.value.trim();
                } else {
                    delete figureChangeDescriptions[figureId];
                }
            });

            // Delete button listener
            const deleteButton = document.getElementById(`delete-${index}`);
            deleteButton.addEventListener('click', () => {
                if (figuresToDelete.has(figureId)) {
                    // Undo delete
                    figuresToDelete.delete(figureId);
                    deleteButton.classList.remove('deleted');
                    deleteButton.textContent = 'Delete Figure';
                    document.getElementById(`figure-container-${index}`).style.opacity = '1';
                    delete figureChangeDescriptions[figureId];
                } else {
                    // Mark for deletion
                    figuresToDelete.add(figureId);
                    deleteButton.classList.add('deleted');
                    deleteButton.textContent = 'Undo Delete';
                    document.getElementById(`figure-container-${index}`).style.opacity = '0.5';
                    figureChangeDescriptions[figureId] = 'delete';
                    
                    // Uncheck and hide comment if it was selected
                    const checkbox = document.getElementById(`comment-checkbox-${index}`);
                    const comment = document.getElementById(`comment-${index}`);
                    checkbox.checked = false;
                    comment.classList.add('hidden');
                    comment.value = '';
                }
            });
        }
    });

    showScreen('figureReview');
}

// Handle explanation review submission
async function handleExplanationReviewSubmit() {
    const changeCheckbox = document.getElementById('explanationChangeCheckbox');
    const commentTextarea = document.getElementById('explanationComment');

    const payload = {
        concept_id: currentConceptId,
        type: 'explanation',
        decision: {
            change: changeCheckbox.checked,
            comment: changeCheckbox.checked ? commentTextarea.value.trim() : ''
        }
    };

    if (changeCheckbox.checked && !payload.decision.comment) {
        showError('Please provide comments for the changes you want to make.');
        return;
    }

    showScreen('loading');
    setLoadingMessage('Processing your feedback...');

    try {
        await resumeAgentHITL(payload);
    } catch (error) {
        console.error('Error resuming agent:', error);
        showError('Failed to submit review. Please try again.');
        showScreen('explanationReview');
    }
}

// Handle figure review submission
async function handleFigureReviewSubmit() {
    const hasChanges = Object.keys(figureChangeDescriptions).length > 0;

    const payload = {
        concept_id: currentConceptId,
        type: 'figure',
        decision: {
            change: hasChanges,
            change_descriptions: hasChanges ? figureChangeDescriptions : {}
        }
    };

    showScreen('loading');
    setLoadingMessage('Processing your feedback...');

    try {
        await resumeAgentHITL(payload);
    } catch (error) {
        console.error('Error resuming agent:', error);
        showError('Failed to submit review. Please try again.');
        showScreen('figureReview');
    }
}

function resumeAgentHITL(payload) {
    return new Promise((resolve, reject) => {
        const url = `${API_BASE_URL}/hitl/resume_agent_hitl`;
        
        console.log('Resuming agent with payload:', payload);
        workflowEnded = false; // Reset flag

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to resume agent');
            }

            console.log('Resume response received, starting stream...');
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let currentEvent = {};

            function readStream() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        console.log('Stream ended');
                        // If workflow ended normally, we've already shown final review
                        // If it ended with interrupt, handleSSEEvent already handled it
                        resolve();
                        return;
                    }

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    
                    buffer = lines.pop() || '';

                    lines.forEach(line => {
                        line = line.trim();
                        
                        if (line.startsWith('event:')) {
                            currentEvent.event = line.slice(6).trim();
                            console.log('Event type:', currentEvent.event);
                        } else if (line.startsWith('id:')) {
                            currentEvent.id = line.slice(3).trim();
                            if (currentEvent.id) {
                                currentConceptId = currentEvent.id;
                            }
                        } else if (line.startsWith('data:')) {
                            currentEvent.data = line.slice(5).trim();
                        } else if (line === '') {
                            if (currentEvent.event && currentEvent.data) {
                                try {
                                    const parsedData = JSON.parse(currentEvent.data);
                                    console.log('Parsed event data:', parsedData);
                                    // Use async/await to ensure proper handling
                                    handleSSEEvent(currentEvent.event, parsedData).catch(err => {
                                        console.error('Error in handleSSEEvent:', err);
                                    });
                                } catch (error) {
                                    console.error('Error parsing event data:', error, currentEvent.data);
                                }
                            }
                            currentEvent = {};
                        }
                    });

                    readStream();
                }).catch(error => {
                    console.error('Stream read error:', error);
                    reject(error);
                });
            }

            readStream();
        })
        .catch(error => {
            console.error('Resume fetch error:', error);
            reject(error);
        });
    });
}

// Show final review screen
async function showFinalReview() {
    try {
        setLoadingMessage('Loading final review...');
        const explanationData = await fetchExplanationData(true);
        displayFinalReview(explanationData);
    } catch (error) {
        console.error('Error loading final review:', error);
        showError('Failed to load final review. Please try again.');
    }
}

// Display final review screen
function displayFinalReview(data) {
    document.getElementById('finalContextText').textContent = data.context;
    document.getElementById('finalConclusionText').textContent = data.conclusion;

    const stepsContainer = document.getElementById('finalStepsContainer');
    stepsContainer.innerHTML = '';

    data.steps.forEach((step, index) => {
        const stepDiv = document.createElement('div');
        stepDiv.className = 'step-item';
        
        let stepHTML = `<div class="step-text">${step.text}</div>`;
        
        if (step.figure) {
            stepHTML += `
                <div class="figure-container">
                    <img src="data:image/png;base64,${step.figure}" alt="Figure ${index}">
                </div>
            `;
        }
        
        stepDiv.innerHTML = stepHTML;
        stepsContainer.appendChild(stepDiv);
    });

    showScreen('finalReview');
}

// Handle upload to cloud
async function handleUploadToCloud() {
    const uploadButton = document.getElementById('uploadToCloud');
    uploadButton.disabled = true;
    uploadButton.textContent = 'Uploading...';

    try {
        const response = await fetch(`${API_BASE_URL}/crud/add_to_cloud/?concept_id=${currentConceptId}`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.status === '200') {
            showScreen('success');
        } else {
            throw new Error(result.data || 'Upload failed');
        }
    } catch (error) {
        console.error('Error uploading to cloud:', error);
        showError('Failed to upload to cloud. Please try again.');
        uploadButton.disabled = false;
        uploadButton.textContent = 'Upload to Cloud';
    }
}

// Screen management helpers
function showScreen(screenName) {
    Object.values(screens).forEach(screen => screen.classList.remove('active'));
    screens[screenName].classList.add('active');
}

function setLoadingMessage(message) {
    document.getElementById('loadingMessage').textContent = message;
}

// Error handling
function showError(message) {
    const errorElement = document.getElementById('errorMessage');
    errorElement.textContent = message;
    errorElement.classList.remove('hidden');
    
    setTimeout(() => {
        errorElement.classList.add('hidden');
    }, 5000);
}

// Reset to initial state
function resetToInitial() {
    currentConceptId = null;
    currentConceptName = null;
    figureChangeDescriptions = {};
    figuresToDelete = new Set();
    
    document.getElementById('conceptInput').value = '';
    showScreen('initial');
}