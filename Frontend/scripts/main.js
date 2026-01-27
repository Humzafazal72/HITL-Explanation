let currentConceptId = null;
let currentEventSource = null;
let figureData = {};
let explanationData = {};
let allFigures = [];
let stepsWithFigures = [];

const API_BASE = "http://localhost:8000"; // Set your API base URL here

function showScreen(screenId) {
  document
    .querySelectorAll(".screen")
    .forEach((s) => s.classList.remove("active"));
  document.getElementById(screenId).classList.add("active");
}

function addLogEntry(message, node = "") {
  const log = document.getElementById("statusLog");
  const entry = document.createElement("div");
  entry.className = "log-entry";
  const timestamp = new Date().toLocaleTimeString();
  entry.innerHTML = `<strong>[${timestamp}]${node ? " " + node : ""}</strong>: ${message}`;
  log.appendChild(entry);
  log.scrollTop = log.scrollHeight;
}

async function startGeneration() {
  const concept = document.getElementById("conceptInput").value.trim();
  if (!concept) {
    alert("Please enter a concept name");
    return;
  }

  showScreen("processingScreen");
  document.getElementById("statusLog").innerHTML = "";
  addLogEntry("Starting generation process...");

  const eventSource = new EventSource(
    `${API_BASE}/hitl/start_agent_hitl?concept=${encodeURIComponent(concept)}`,
  );
  currentEventSource = eventSource;

  eventSource.onmessage = (event) => {
    handleSSEMessage(event);
  };

  eventSource.addEventListener("explainer", (event) => {
    addLogEntry("Generating explanation...", "explainer");
  });

  eventSource.addEventListener("explanation_reviewer", (event) => {
    const data = JSON.parse(event.data);
    currentConceptId = data.concept_id;
    addLogEntry("Reviewing explanation...", "explanation_reviewer");
  });

  eventSource.addEventListener("__interrupt__", (event) => {
    const data = JSON.parse(event.data);
    currentConceptId = data.concept_id;
    handleInterrupt(data);
  });

  eventSource.addEventListener("async_explanation_processor", (event) => {
    addLogEntry("Processing explanation...", "async_explanation_processor");
  });

  eventSource.addEventListener("contextual_prompt_generator", (event) => {
    addLogEntry(
      "Generating contextual prompts...",
      "contextual_prompt_generator",
    );
  });

  eventSource.addEventListener("async_coder_hitl", (event) => {
    addLogEntry("Generating figures...", "async_coder_hitl");
  });

  eventSource.addEventListener("fig_reviewer", (event) => {
    addLogEntry("Reviewing figures...", "fig_reviewer");
  });

  eventSource.addEventListener("async_fig_fixer", (event) => {
    addLogEntry("Fixing figures...", "async_fig_fixer");
  });

  eventSource.addEventListener("__END__", (event) => {
    addLogEntry("Process completed!");
    eventSource.close();
    showFinalReview();
  });

  eventSource.onerror = (error) => {
    console.error("EventSource error:", error);
    eventSource.close();
  };
}

function handleSSEMessage(event) {
  // Generic message handler
}

async function handleInterrupt(data) {
  currentEventSource.close();

  if (data.payload && data.payload.type === "explanation") {
    await showExplanationReview();
  } else if (data.payload && data.payload.type === "figure") {
    showFigureReview(data.payload);
  }
}

async function showExplanationReview() {
  try {
    // Fetch explanation data from the API
    const response = await fetch(
      `${API_BASE}/crud/get_data/?concept_id=${currentConceptId}&diagrams=false`,
    );
    const data = await response.json();

    // Store for later use
    explanationData = data;
    stepsWithFigures = data.steps;

    const content = document.getElementById("explanationContent");

    // Build steps HTML with figures
    let stepsHTML = "";
    data.steps.forEach((step, index) => {
      stepsHTML += `
                        <li>
                            <p>${step.text}</p>
                            ${
                              step.figure
                                ? `
                                <div style="margin: 15px 0; text-align: center;">
                                    <img src="data:image/png;base64,${step.figure}" 
                                         alt="Figure ${index}" 
                                         style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                    <p style="font-size: 0.9em; color: #666; margin-top: 8px;">Figure ${index + 1}</p>
                                </div>
                            `
                                : ""
                            }
                        </li>
                    `;
    });

    content.innerHTML = `
                    <div class="explanation-section">
                        <h3>Context</h3>
                        <p>${data.context || "N/A"}</p>
                    </div>
                    <div class="explanation-section">
                        <h3>Explanation Steps</h3>
                        <ol style="list-style-position: outside;">
                            ${stepsHTML}
                        </ol>
                    </div>
                    <div class="explanation-section">
                        <h3>Conclusion</h3>
                        <p>${data.conclusion || "N/A"}</p>
                    </div>
                `;

    showScreen("explanationReviewScreen");
  } catch (error) {
    console.error("Error fetching explanation data:", error);
    addLogEntry("Error loading explanation data: " + error.message);
    alert("Error loading explanation. Please try again.");
  }
}

function toggleExplanationComment() {
  const checkbox = document.getElementById("needChangesExplanation");
  const commentBox = document.getElementById("explanationCommentBox");

  if (checkbox.checked) {
    commentBox.classList.add("active");
  } else {
    commentBox.classList.remove("active");
  }
}

async function submitExplanationReview() {
  const needChanges = document.getElementById("needChangesExplanation").checked;
  const comment = document.getElementById("explanationComment").value.trim();

  const payload = {
    concept_id: parseInt(currentConceptId),
    type: "explanation",
    decision: {
      change: needChanges,
      comment: needChanges ? comment : "",
    },
  };

  showScreen("processingScreen");
  addLogEntry("Submitting explanation review...");

  const response = await fetch(`${API_BASE}/hitl/resume_agent_hitl`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split("\n\n");

    for (const line of lines) {
      if (line.startsWith("event:")) {
        const eventMatch = line.match(/event: (.+)/);
        const dataMatch = line.match(/data: (.+)/);

        if (eventMatch && dataMatch) {
          const eventName = eventMatch[1];
          const eventData = JSON.parse(dataMatch[1]);

          if (eventName === "__interrupt__") {
            await handleInterrupt(eventData);
          } else if (eventName === "__END__") {
            await showFinalReview();
          } else {
            addLogEntry(`Processing ${eventName}...`, eventName);
          }
        }
      }
    }
  }
}

function showFigureReview(payload) {
  allFigures = payload.figures || [];
  figureData = {};

  const container = document.getElementById("figuresContainer");
  container.innerHTML = "";

  allFigures.forEach((figureName) => {
    const card = document.createElement("div");
    card.className = "figure-card";
    card.id = `figure-card-${figureName}`;
    card.innerHTML = `
                    <h4>${figureName}</h4>
                    <img src="${API_BASE}/Storage/${currentConceptId}/${figureName}.png" alt="${figureName}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22300%22 height=%22200%22%3E%3Crect fill=%22%23ddd%22 width=%22300%22 height=%22200%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 fill=%22%23999%22%3EImage not found%3C/text%3E%3C/svg%3E'">
                    <div class="figure-actions">
                        <button class="button-danger" onclick="deleteFigure('${figureName}')">Delete</button>
                        <button class="button-secondary" onclick="toggleFigureComment('${figureName}')">Add Comment</button>
                    </div>
                    <div id="comment-${figureName}" class="comment-input">
                        <textarea id="textarea-${figureName}" placeholder="Describe improvements..."></textarea>
                    </div>
                `;
    container.appendChild(card);

    figureData[figureName] = { action: "keep", comment: "" };
  });

  showScreen("figureReviewScreen");
}

function deleteFigure(figureName) {
  figureData[figureName] = { action: "delete", comment: "" };
  const card = event.target.closest(".figure-card");
  card.style.opacity = "0.5";
  card.style.border = "2px solid #dc3545";
}

function toggleFigureComment(figureName) {
  const commentBox = document.getElementById(`comment-${figureName}`);
  commentBox.classList.toggle("active");
}

async function submitFigureReview() {
  const changeDescriptions = {};
  let hasChanges = false;

  for (const [figureName, data] of Object.entries(figureData)) {
    const textarea = document.getElementById(`textarea-${figureName}`);
    const comment = textarea ? textarea.value.trim() : "";

    if (data.action === "delete") {
      changeDescriptions[figureName] = "delete";
      hasChanges = true;
    } else if (comment) {
      changeDescriptions[figureName] = comment;
      hasChanges = true;
    }
  }

  const payload = {
    concept_id: parseInt(currentConceptId),
    type: "figure",
    decision: {
      change: hasChanges,
      change_descriptions: changeDescriptions,
    },
  };

  showScreen("processingScreen");
  addLogEntry("Submitting figure review...");

  const response = await fetch(`${API_BASE}/hitl/resume_agent_hitl`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split("\n\n");

    for (const line of lines) {
      if (line.startsWith("event:")) {
        const eventMatch = line.match(/event: (.+)/);
        const dataMatch = line.match(/data: (.+)/);

        if (eventMatch && dataMatch) {
          const eventName = eventMatch[1];
          const eventData = JSON.parse(dataMatch[1]);

          if (eventName === "__interrupt__") {
            await handleInterrupt(eventData);
          } else if (eventName === "__END__") {
            await showFinalReview();
          } else {
            addLogEntry(`Processing ${eventName}...`, eventName);
          }
        }
      }
    }
  }
}

async function showFinalReview() {
  // Fetch data with diagrams using the new endpoint
  try {
    const response = await fetch(
      `${API_BASE}/crud/get_data/?concept_id=${currentConceptId}&diagrams=true`,
    );
    const data = await response.json();

    stepsWithFigures = data.steps;

    const explanationContent = document.getElementById(
      "finalExplanationContent",
    );

    // Build steps HTML with figures
    let stepsHTML = "";
    data.steps.forEach((step, index) => {
      stepsHTML += `
                        <li>
                            <p>${step.text}</p>
                            ${
                              step.figure
                                ? `
                                <div style="margin: 15px 0; text-align: center;">
                                    <img src="data:image/png;base64,${step.figure}" 
                                         alt="Figure ${index}" 
                                         style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                    <p style="font-size: 0.9em; color: #666; margin-top: 8px;">Figure ${index + 1}</p>
                                </div>
                            `
                                : ""
                            }
                        </li>
                    `;
    });

    explanationContent.innerHTML = `
                    <h2>Complete Explanation</h2>
                    <div class="explanation-section">
                        <h3>Context</h3>
                        <p>${data.context}</p>
                    </div>
                    <div class="explanation-section">
                        <h3>Explanation Steps</h3>
                        <ol style="list-style-position: outside;">
                            ${stepsHTML}
                        </ol>
                    </div>
                    <div class="explanation-section">
                        <h3>Conclusion</h3>
                        <p>${data.conclusion}</p>
                    </div>
                `;

    // Clear the figures content section as figures are now embedded
    document.getElementById("finalFiguresContent").innerHTML = "";

    showScreen("finalReviewScreen");
  } catch (error) {
    console.error("Error fetching final data:", error);
    alert("Error loading final review. Please try again.");
  }
}

async function uploadToCloud() {
  try {
    const response = await fetch(
      `${API_BASE}/crud/add_to_cloud/?concept_id=${currentConceptId}`,
      {
        method: "POST",
      },
    );

    const result = await response.json();

    if (result.status === "200") {
      showScreen("successScreen");
    } else {
      alert("Error uploading to cloud: " + result.data);
    }
  } catch (error) {
    alert("Error uploading to cloud: " + error.message);
  }
}

function resetApp() {
  currentConceptId = null;
  figureData = {};
  explanationData = {};
  allFigures = [];
  document.getElementById("conceptInput").value = "";
  document.getElementById("needChangesExplanation").checked = false;
  document.getElementById("explanationComment").value = "";
  toggleExplanationComment();
  showScreen("initialScreen");
}
