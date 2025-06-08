// main.js
document.addEventListener("DOMContentLoaded", () => {
  // --- Landing & Chat Toggle Elements ---
  const openChatBtn  = document.getElementById("open-chat");
  const chatToggle   = document.getElementById("chat-toggle");
  const chatWidget   = document.getElementById("chat-widget");

  // --- Chat UI Elements ---
  const messagesDiv  = document.getElementById("messages");
  const textInput    = document.getElementById("text-input");
  const sendButton   = document.getElementById("send-button");
  const fileInput    = document.getElementById("file-input");
  const loader       = document.getElementById("loader");

  const userId       = "frontend_user";

  // Flags for image-upload steps
  let expectingAadhaar   = true;
  let expectingDischarge = false;

  // Hide chat on load
  chatWidget.classList.add("hidden");
  chatToggle.classList.add("hidden");

  // --- Toggle Handlers ---
  openChatBtn.addEventListener("click", () => {
    chatWidget.classList.remove("hidden");
    chatToggle.classList.remove("hidden");
    // scroll chat into view
    chatWidget.scrollIntoView({ behavior: "smooth" });
  });

  chatToggle.addEventListener("click", () => {
    chatWidget.classList.toggle("hidden");
  });

  // --- Loader Helpers ---
  function showLoader() { loader.classList.remove("hidden"); }
  function hideLoader() { loader.classList.add("hidden"); }

  // --- Message Rendering ---
  function appendMessage(text, role) {
    const div = document.createElement("div");
    div.className = `message ${role}`;
    if (role === "bot") {
      // render markdown for bot
      div.innerHTML = marked.parse(text);
    } else {
      div.textContent = text;
    }
    messagesDiv.appendChild(div);
    // fade in
    requestAnimationFrame(() => div.classList.add("visible"));
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  function appendHTML(htmlString) {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = htmlString.trim();
    messagesDiv.appendChild(wrapper);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  // --- Chat Request ---
  async function sendToChat(content, isImage = false) {
    showLoader();

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, last_input: content })
      });
      const data = await res.json();
      hideLoader();

      // show the user’s message (or image label)
      if (isImage) {
        let label = "[Image]";
        if (expectingAadhaar)    label = "Aadhaar card loaded";
        else if (expectingDischarge) label = "Discharge summary loaded";
        appendMessage(label, "user");
      } else {
        appendMessage(content, "user");
      }

      // show bot reply
      if (data.bot_message) appendMessage(data.bot_message, "bot");

      // show visiting card snippet (if provided)
      if (data.visiting_card_html) appendHTML(data.visiting_card_html);

      // adjust upload flags based on bot prompts/responses
      const botText = (data.bot_message || "").toLowerCase();

      if (botText.includes("please upload a photo of your aadhaar")) {
        expectingAadhaar   = true;
        expectingDischarge = false;
      }
      if (data.aadhaar_fields) {
        expectingAadhaar   = false;
        expectingDischarge = false;
      }
      if (botText.includes("do you have a discharge summary")) {
        expectingDischarge = true;
      }
      if (botText.startsWith("here is your discharge summary")
          || botText.startsWith("medical history:")) {
        expectingDischarge = false;
      }

    } catch (err) {
      hideLoader();
      appendMessage("Network error: " + err, "bot");
    }
  }

  // --- Input Event Handlers ---
  sendButton.addEventListener("click", () => {
    const txt = textInput.value.trim();
    if (!txt) return;
    sendToChat(txt, false);
    textInput.value = "";
  });

  textInput.addEventListener("keydown", e => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendButton.click();
    }
  });

  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      sendToChat(reader.result, true);
    };
    reader.readAsDataURL(file);
    fileInput.value = "";
  });

  // --- Kick off conversation ---
  sendToChat("Hi", false);
});
