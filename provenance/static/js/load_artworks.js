const div = document.getElementById("results");
div.innerHTML = "Se încarcă...";

let currentPage = 1;
let totalPages = 1;
let totalArtworks = 0;
const itemsPerPage = 50;

// Helper to validate birth date
function isValidBirthDate(dateStr) {
  if (!dateStr) return false;
  if (dateStr.startsWith('-') || dateStr.includes('0000-') || dateStr.includes('-00-00')) {
    return false;
  }
  const year = parseInt(dateStr.split('-')[0], 10);
  if (year < 1000 || year > 2100) {
    return false;
  }
  return true;
}

function renderArtworks(pageData, page) {
  let html = `
    <div style="margin-bottom: 20px; padding: 10px; background: #f0f0f0; border-radius: 4px;">
      <strong>Pagina ${page} din ${totalPages}</strong> | Total: ${totalArtworks} opere
      <br>
      <button onclick="fetchPage(${page - 1})" ${page === 1 ? 'disabled' : ''} style="margin-right: 10px; padding: 8px 15px;">← Anterior</button>
      <button onclick="fetchPage(${page + 1})" ${page === totalPages ? 'disabled' : ''} style="padding: 8px 15px;">Următor →</button>
    </div>
  `;
  
  html += pageData.map(o => {
    const validBirthDate = isValidBirthDate(o.dbpedia?.birthDate);
    const birthLine = validBirthDate 
      ? `Naștere: ${o.dbpedia.birthDate} în ${o.dbpedia.birthPlace || 'N/A'}<br>`
      : '';
    
    return `
      <div style="margin-bottom:15px; border-bottom:1px solid #ccc; padding:5px;">
        <strong>${o.title}</strong><br>
        Autor: ${o.creator}<br>
        An: ${o.date || 'N/A'}<br>
        Muzeu: ${o.museum || 'N/A'}<br>
        Curent artistic: ${o.movement || 'N/A'}<br>
        ${o.dbpedia ? `
          ${birthLine}
          Naționalitate: ${o.dbpedia.nationality || 'N/A'}${o.dbpedia.movement ? `<br>Mișcare artistică (creator): ${o.dbpedia.movement}` : ''}
        ` : ''}
      </div>
    `;
  }).join("");
  
  html += `
    <div style="margin-top: 20px; padding: 10px; background: #f0f0f0; border-radius: 4px;">
      <button onclick="fetchPage(${page - 1})" ${page === 1 ? 'disabled' : ''} style="margin-right: 10px; padding: 8px 15px;">← Anterior</button>
      <button onclick="fetchPage(${page + 1})" ${page === totalPages ? 'disabled' : ''} style="padding: 8px 15px;">Următor →</button>
    </div>
  `;
  
  div.innerHTML = html;
  window.scrollTo(0, 0);
}

function fetchPage(page) {
  if (page < 1 || page > totalPages) return;
  currentPage = page;
  
  div.innerHTML = `<p>Se încarcă pagina ${page}...</p>`;
  
  fetch(`/api/?page=${page}&per_page=${itemsPerPage}`)
    .then(r => r.json())
    .then(data => {
        totalPages = data.total_pages;
        totalArtworks = data.total;
        renderArtworks(data.items, data.page);
    })
    .catch(err => {
      div.innerHTML = `<p style="color: red;">Eroare: ${err.message}</p>`;
    });
}

// Load first page immediately
fetchPage(1);
