const articlesContainer = document.getElementById("articles");
const searchInput = document.getElementById("search-input");
const generateButton = document.getElementById("generate-button");
const statusPanel = document.getElementById("agent-status");
const statusMessage = document.getElementById("status-message");
let articles = [];
let statusPoll;

document.getElementById("current-date").textContent = new Intl.DateTimeFormat("en", {
    month: "long",
    day: "numeric",
    year: "numeric",
}).format(new Date());

async function requestJson(url, options) {
    const response = await fetch(url, options);
    const payload = await response.json();
    if (!response.ok) {
        throw new Error(payload.error || "The request could not be completed.");
    }
    return payload;
}

async function loadJournal() {
    try {
        const [posts, topicData, status] = await Promise.all([
            requestJson("/api/posts"),
            requestJson("/api/topics"),
            requestJson("/api/status"),
        ]);
        articles = posts;
        renderArticles();
        renderTopics(topicData.topics);
        showStatus(status);
        if (status.status === "running") {
            beginStatusPolling();
        }
    } catch (error) {
        articlesContainer.replaceChildren(createMessage(
            "The journal could not be reached. Refresh the page to try again.",
            "feed-error",
        ));
        showStatus({ status: "failed", message: error.message });
    }
}

function createMessage(message, className = "feed-message") {
    const element = document.createElement("p");
    element.className = className;
    element.textContent = message;
    return element;
}

function renderArticles() {
    const query = searchInput.value.trim().toLocaleLowerCase();
    const visibleArticles = articles.filter(article =>
        [article.topic, article.title, article.content, ...article.tags]
            .join(" ")
            .toLocaleLowerCase()
            .includes(query),
    );
    document.getElementById("post-count").textContent = articles.length;
    articlesContainer.replaceChildren();

    if (visibleArticles.length === 0) {
        articlesContainer.appendChild(createMessage(
            query ? "No dispatches match that search." : "No dispatches yet. Start the editorial desk when you're ready.",
        ));
        return;
    }

    visibleArticles.forEach((article, index) => {
        articlesContainer.appendChild(createArticle(article, index));
    });
}

function createArticle(article, index) {
    const articleElement = document.createElement("article");
    articleElement.className = "article-entry";

    const metadata = document.createElement("div");
    metadata.className = "article-meta";
    const number = document.createElement("span");
    number.className = "article-number";
    number.textContent = String(index + 1).padStart(2, "0");
    const topic = document.createElement("span");
    topic.className = "article-topic";
    topic.textContent = article.topic || "Dispatch";
    const date = document.createElement("time");
    date.className = "article-date";
    date.textContent = article.date;
    metadata.append(number, topic, date);

    const title = document.createElement("h3");
    title.textContent = article.title;
    const content = document.createElement("p");
    content.className = "article-content";
    content.textContent = article.content;

    const tags = document.createElement("div");
    tags.className = "tags";
    article.tags.forEach(tag => {
        const tagElement = document.createElement("span");
        tagElement.className = "tag";
        tagElement.textContent = `#${tag}`;
        tags.appendChild(tagElement);
    });

    articleElement.append(metadata, title, content, tags);
    return articleElement;
}

function renderTopics(topics) {
    const topicList = document.getElementById("topic-list");
    document.getElementById("topic-count").textContent = `${topics.length} ${topics.length === 1 ? "topic" : "topics"}`;
    topicList.replaceChildren();

    if (topics.length === 0) {
        const item = document.createElement("li");
        item.className = "topic-placeholder";
        item.textContent = "No topics yet.";
        topicList.appendChild(item);
        return;
    }

    topics.forEach(topic => {
        const item = document.createElement("li");
        item.textContent = topic;
        topicList.appendChild(item);
    });
}

function showStatus(status) {
    const labels = {
        idle: "The editorial desk is ready.",
        running: "Researching and drafting a new post.",
        succeeded: "A new post has been published.",
        failed: status.message || "Generation failed. Check the server logs.",
    };
    statusPanel.dataset.state = status.status;
    statusMessage.textContent = labels[status.status] || status.message || "The editorial desk is ready.";
    generateButton.disabled = status.status === "running";
    generateButton.querySelector("span:last-child").textContent = status.status === "running"
        ? "Generating story"
        : "Generate a story";
}

function beginStatusPolling() {
    if (statusPoll) {
        return;
    }
    statusPoll = window.setInterval(async () => {
        try {
            const status = await requestJson("/api/status");
            showStatus(status);
            if (status.status !== "running") {
                window.clearInterval(statusPoll);
                statusPoll = undefined;
                if (status.status === "succeeded") {
                    await loadJournal();
                }
            }
        } catch (error) {
            statusMessage.textContent = error.message;
        }
    }, 2500);
}

generateButton.addEventListener("click", async () => {
    let token = sessionStorage.getItem("tweety-generation-key");
    if (!token) {
        token = window.prompt("Enter the generation key configured for this journal:");
        if (!token) {
            return;
        }
        sessionStorage.setItem("tweety-generation-key", token);
    }
    generateButton.disabled = true;
    try {
        const status = await requestJson("/api/run", {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
        });
        showStatus(status);
        beginStatusPolling();
    } catch (error) {
        if (error.message.includes("generation key")) {
            sessionStorage.removeItem("tweety-generation-key");
        }
        showStatus({ status: "failed", message: error.message });
    }
});

searchInput.addEventListener("input", renderArticles);
loadJournal();