const $ = (selector, parent = document) => parent.querySelector(selector);
const $$ = (selector, parent = document) => [...parent.querySelectorAll(selector)];
const SAMPLE_PUZZLE = [7, 2, 4, 5, 0, 6, 8, 3, 1];
const SAMPLES = {
  4: [[1,0,0,4],[0,4,1,0],[0,1,4,0],[4,0,0,1]],
  9: [[5,3,0,0,7,0,0,0,0],[6,0,0,1,9,5,0,0,0],[0,9,8,0,0,0,0,6,0],[8,0,0,0,6,0,0,0,3],[4,0,0,8,0,3,0,0,1],[7,0,0,0,2,0,0,0,6],[0,6,0,0,0,0,2,8,0],[0,0,0,4,1,9,0,0,5],[0,0,0,0,8,0,0,7,9]],
};
let puzzleTrace = [];
let pathIndex = 0;
let latestSudoku = null;

function setTab(name) {
  const puzzle = name === 'puzzle';
  $('#tab-puzzle').classList.toggle('active', puzzle);
  $('#tab-sudoku').classList.toggle('active', !puzzle);
  $('#tab-puzzle').setAttribute('aria-selected', String(puzzle));
  $('#tab-sudoku').setAttribute('aria-selected', String(!puzzle));
  $('#panel-puzzle').hidden = !puzzle;
  $('#panel-sudoku').hidden = puzzle;
}
$('#tab-puzzle').addEventListener('click', () => setTab('puzzle'));
$('#tab-sudoku').addEventListener('click', () => setTab('sudoku'));

function buildPuzzleInput(values = Array(9).fill(null)) {
  const root = $('#puzzle-input');
  root.replaceChildren();
  values.forEach((value, index) => {
    const input = document.createElement('input');
    input.className = 'puzzle-cell';
    input.type = 'text';
    input.inputMode = 'numeric';
    input.maxLength = 1;
    input.autocomplete = 'off';
    input.setAttribute('aria-label', `Row ${Math.floor(index / 3) + 1}, column ${index % 3 + 1}${value === 0 ? ', blank tile' : ''}`);
    if (value !== null && value !== 0) input.value = String(value);
    input.placeholder = value === 0 ? '·' : '';
    input.addEventListener('input', () => { input.value = input.value.replace(/[^1-8]/g, '').slice(0, 1); });
    input.addEventListener('keydown', event => {
      if (!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Enter'].includes(event.key)) return;
      event.preventDefault();
      const delta = event.key === 'ArrowLeft' ? -1 : event.key === 'ArrowRight' || event.key === 'Enter' ? 1 : event.key === 'ArrowUp' ? -3 : 3;
      root.children[Math.max(0, Math.min(8, index + delta))]?.focus();
    });
    root.append(input);
  });
}
buildPuzzleInput();
$('#sample-puzzle').addEventListener('click', () => { buildPuzzleInput(SAMPLE_PUZZLE); $('#puzzle-error').hidden = true; });

function getPuzzleInput() {
  const inputs = $$('.puzzle-cell');
  const raw = inputs.map(input => input.value.trim());
  if (raw.filter(value => value === '').length !== 1) throw new Error('Leave exactly one cell empty for the blank tile.');
  const numbers = raw.filter(Boolean).map(Number);
  if (numbers.length !== 8 || new Set(numbers).size !== 8 || numbers.some(n => n < 1 || n > 8)) {
    throw new Error('Enter every tile from 1 to 8 once, and leave one cell empty.');
  }
  return raw.map(value => value === '' ? 0 : Number(value));
}

async function postJSON(url, body) {
  const response = await fetch(url, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error || 'The solver could not process this board.');
    error.details = data;
    throw error;
  }
  return data;
}

$('#solve-puzzle').addEventListener('click', async () => {
  const error = $('#puzzle-error'); error.hidden = true;
  let state;
  try { state = getPuzzleInput(); } catch (reason) { error.textContent = reason.message; error.hidden = false; return; }
  const button = $('#solve-puzzle'); button.disabled = true; button.firstElementChild.textContent = 'Searching…';
  try {
    const data = await postJSON('/api/puzzle', {state});
    renderPuzzleResults(data);
  } catch (reason) {
    error.textContent = reason.details?.reason
      ? `${reason.details.reason} A* search was not started.`
      : reason.message;
    error.hidden = false;
    if ($('#puzzle-results').hidden) $('#parity-result').textContent = '';
  } finally { button.disabled = false; button.firstElementChild.textContent = 'Solve with A*'; }
});

function renderPuzzleResults(data) {
  const results = data.results;
  $('#puzzle-results').hidden = false;
  $('#parity-result').textContent = `PARITY ${data.inversions % 2 === 0 ? 'EVEN' : 'ODD'} · ${data.inversions} inversions`;
  $('#puzzle-insight').textContent = `${data.comparison} Both heuristics returned an optimal ${results[0].cost}-move solution.`;
  $('#heuristic-metrics').innerHTML = results.map(result => `
    <div class="metric-card ${result.key}"><div class="metric-title">${result.name}</div><div class="metric-label">nodes expanded</div><div class="metric-value">${result.expanded.toLocaleString()}</div></div>`).join('');
  $('#heuristic-table').innerHTML = results.map(result => `<tr><td>${result.name}</td><td>${result.cost}</td><td>${result.expanded.toLocaleString()}</td><td>${result.generated.toLocaleString()}</td></tr>`).join('');
  $('#comparison-footnote').textContent = 'A* uses f(n) = g(n) + h(n). Both heuristics are admissible; Manhattan is more informed because it measures how far each misplaced tile must travel. Node counts depend on the input board.';
  puzzleTrace = data.trace; pathIndex = 0;
  renderPathStep();
  $('#puzzle-results').scrollIntoView({behavior:'smooth', block:'start'});
}

function renderPathStep() {
  if (!puzzleTrace.length) return;
  const item = puzzleTrace[pathIndex];
  const prev = pathIndex ? puzzleTrace[pathIndex - 1] : null;
  const movedTile = prev ? prev.state[item.state.indexOf(0)] : null;
  $('#path-counter').textContent = `STEP ${pathIndex} / ${puzzleTrace.length - 1}`;
  $('#solution-board').innerHTML = item.state.map(value => `<span class="${value === 0 ? 'empty-tile' : value === movedTile ? 'just-moved' : ''}">${value || ''}</span>`).join('');
  $('#path-prev').disabled = pathIndex === 0;
  $('#path-next').disabled = pathIndex === puzzleTrace.length - 1;
  const progress = $('#path-progress');
  progress.replaceChildren();
  const stride = puzzleTrace.length > 32 ? Math.ceil(puzzleTrace.length / 32) : 1;
  const shown = [...new Set([...Array.from({length: Math.ceil(puzzleTrace.length / stride)}, (_,i)=>i*stride), puzzleTrace.length - 1])];
  shown.forEach(index => {
    const dot = document.createElement('button'); dot.className = `progress-dot ${index === pathIndex ? 'active' : ''}`;
    dot.setAttribute('aria-label', `Go to step ${index}`); dot.title = `Step ${index}`;
    dot.addEventListener('click', () => { pathIndex = index; renderPathStep(); }); progress.append(dot);
  });
  const previousHint = prev?.hint;
  $('#move-readout').innerHTML = previousHint ? `Moved tile <strong>${previousHint.tile}</strong> ${previousHint.move.toLowerCase()} into the blank` : 'Starting board';
  $('#h-badge').textContent = `h = ${item.h}`;
  $('#contribution-list').innerHTML = item.tiles.map(tile => `<div class="tile-contribution"><b>Tile ${tile.tile}</b><small>${tile.distance} step${tile.distance === 1 ? '' : 's'}</small></div>`).join('');
  const hint = item.hint;
  $('#hint-box').innerHTML = hint ? `<strong>Hint: move ${hint.move.toLowerCase()}.</strong> Slide tile ${hint.tile}. It is the next action on the optimal A* path. Its score is <strong>f = g + h = ${hint.g} + ${hint.h} = ${hint.f}</strong>.` : '<strong>Goal reached.</strong> Every numbered tile is in its target cell, so h = 0.';
  $('#successor-list').innerHTML = hint ? `<div class="successor-title">LEGAL NEXT MOVES · f = g + h</div>${item.successors.map(next => `<div class="successor-row ${next.chosen ? 'chosen' : ''}"><span>${next.move}${next.chosen ? ' · chosen on optimal path' : ''}</span><span>${next.g} + ${next.h} = ${next.f}</span></div>`).join('')}` : '';
}
$('#path-prev').addEventListener('click', () => { pathIndex = Math.max(0, pathIndex - 1); renderPathStep(); });
$('#path-next').addEventListener('click', () => { pathIndex = Math.min(puzzleTrace.length - 1, pathIndex + 1); renderPathStep(); });

function buildSudoku(size, values = null, target = '#sudoku-input', locked = false) {
  const root = $(target); root.replaceChildren();
  root.classList.toggle('sudoku-grid-4', size === 4); root.classList.toggle('sudoku-grid-9', size === 9);
  const flat = values ? values.flat() : Array(size * size).fill(0);
  flat.forEach((value, index) => {
    const input = document.createElement('input'); input.className = 'sudoku-cell';
    input.type = 'text'; input.inputMode = 'numeric'; input.maxLength = String(size).length;
    input.setAttribute('aria-label', `Row ${Math.floor(index / size) + 1}, column ${index % size + 1}`);
    if (value) input.value = String(value);
    if (locked) { input.readOnly = true; input.classList.add('given'); }
    else input.addEventListener('input', () => { input.value = input.value.replace(/[^1-9]/g, '').slice(0, String(size).length); });
    root.append(input);
  });
}
function sudokuSize() { return Number($('#sudoku-size').value); }
buildSudoku(4);
$('#sudoku-size').addEventListener('change', () => { buildSudoku(sudokuSize()); $('#sudoku-results').hidden = true; $('#sudoku-error').hidden = true; });
$('#sample-sudoku').addEventListener('click', () => { buildSudoku(sudokuSize(), SAMPLES[sudokuSize()]); $('#sudoku-error').hidden = true; });
function getSudokuInput(size) {
  const values = $$('.sudoku-cell', $('#sudoku-input')).map(input => input.value.trim() === '' ? 0 : Number(input.value));
  if (values.some(value => value < 0 || value > size)) throw new Error(`Use values from 1 to ${size}; leave empty cells blank.`);
  return Array.from({length:size}, (_,row) => values.slice(row * size, (row + 1) * size));
}
$('#solve-sudoku').addEventListener('click', async () => {
  const error = $('#sudoku-error'); error.hidden = true;
  const size = sudokuSize(); let grid;
  try { grid = getSudokuInput(size); } catch (reason) { error.textContent = reason.message; error.hidden = false; return; }
  if (grid.flat().every(value => value === 0)) { error.textContent = 'Enter at least a few clues, or load the example board.'; error.hidden = false; return; }
  const button = $('#solve-sudoku'); button.disabled = true; button.firstElementChild.textContent = 'Comparing…';
  try { const data = await postJSON('/api/sudoku', {size, grid}); renderSudokuResults(data); }
  catch (reason) { error.textContent = reason.message; error.hidden = false; }
  finally { button.disabled = false; button.firstElementChild.textContent = 'Compare all 4 methods'; }
});
function renderSudokuResults(data) {
  latestSudoku = data;
  $('#sudoku-results').hidden = false;
  const solvedCount = data.results.filter(result => result.grid).length;
  $('#sudoku-status').textContent = solvedCount === 4 ? `${data.size}×${data.size} · ALL FOUR SOLVED` : `${data.size}×${data.size} · ${solvedCount}/4 SOLVED`;
  $('#sudoku-table').innerHTML = data.results.map(result => `<tr><td>${result.name}</td><td>${result.assignments.toLocaleString()}</td><td>${result.backtracks.toLocaleString()}</td><td>${(result.runtime_seconds * 1000).toFixed(3)} ms</td></tr>`).join('');
  $('#method-notes').innerHTML = [
    ['Plain backtracking','Chooses the first empty cell and tries legal values.'],
    ['MRV','Branches on the cell with the fewest candidates.'],
    ['Forward checking','Removes each choice from peer domains and detects empty domains early.'],
    ['AC-3','Propagates binary constraints until arcs are consistent before branching.'],
  ].map(([name, note]) => `<div class="method-note"><strong>${name}</strong>${note}</div>`).join('');
  if (data.solution) {
    $('#sudoku-solution-title').textContent = `${data.size} × ${data.size} solution`;
    buildSudoku(data.size, data.solution, '#sudoku-solution', true);
  } else {
    $('#sudoku-solution-title').textContent = 'No solution found';
    buildSudoku(data.size, Array.from({length:data.size},()=>Array(data.size).fill(0)), '#sudoku-solution', true);
  }
  $('#sudoku-results').scrollIntoView({behavior:'smooth', block:'start'});
}

