console.log("Touch the Grass content script running on", window.location.href);

const keywords = ["urgent", "ASAP", "stress", "deadline"];
const bodyText = document.body.innerHTML;

keywords.forEach(word => {
    const regex = new RegExp(`\\b(${word})\\b`, 'gi');
    document.body.innerHTML = document.body.innerHTML.replace(regex, `<span style="background-color: yellow;">$1</span>`);
});