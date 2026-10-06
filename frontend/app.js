const $ = s => document.querySelector(s);
const msg = t => ($("#msg").textContent = t || "");

async function api(url, method = "GET", body) {
  const r = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await r.json();
  if (!r.ok) { msg(data.error || "Something went wrong"); throw new Error(data.error); }
  msg();
  return data;
}

const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function load() {
  const [books, members, loans] = await Promise.all([api("/api/books"), api("/api/members"), api("/api/loans")]);
  $("#bookRows").innerHTML = books.map(b => `<tr><td>${esc(b.title)}</td><td>${esc(b.author)}</td><td>${esc(b.isbn)}</td>
    <td>${b.available}/${b.copies}</td><td><button onclick="del('books',${b.id})">Delete</button></td></tr>`).join("");
  $("#memberRows").innerHTML = members.map(m => `<tr><td>${esc(m.name)}</td><td>${esc(m.email)}</td>
    <td><button onclick="del('members',${m.id})">Delete</button></td></tr>`).join("");
  $("#bookSel").innerHTML = books.filter(b => b.available > 0).map(b => `<option value="${b.id}">${esc(b.title)}</option>`).join("");
  $("#memberSel").innerHTML = members.map(m => `<option value="${m.id}">${esc(m.name)}</option>`).join("");
  const today = new Date().toISOString().slice(0, 10);
  $("#loanRows").innerHTML = loans.map(l => {
    const late = !l.returned && l.due < today;
    const status = l.returned ? `Returned ${l.returned}` : late ? '<span class="late">Overdue</span>' : "On loan";
    return `<tr><td>${esc(l.title)}</td><td>${esc(l.member)}</td><td>${l.issued}</td><td>${l.due}</td><td>${status}</td>
      <td>${l.returned ? "" : `<button class="ok" onclick="ret(${l.id})">Return</button>`}</td></tr>`;
  }).join("");
}

async function del(kind, id) { await api(`/api/${kind}/${id}`, "DELETE"); load(); }
async function ret(id) { await api(`/api/loans/${id}/return`, "POST"); load(); }

function bind(formId, url) {
  $(formId).addEventListener("submit", async e => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    await api(url, "POST", data);
    e.target.reset();
    load();
  });
}
bind("#bookForm", "/api/books");
bind("#memberForm", "/api/members");
bind("#loanForm", "/api/loans");

document.querySelectorAll("nav button").forEach(btn => btn.addEventListener("click", () => {
  document.querySelectorAll("nav button").forEach(b => b.classList.toggle("active", b === btn));
  document.querySelectorAll("main section").forEach(s => (s.hidden = s.id !== btn.dataset.tab));
}));

load();
