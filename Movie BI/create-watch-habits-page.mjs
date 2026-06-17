import { writeFileSync, mkdirSync, readFileSync } from 'fs';
import { join } from 'path';

const projectBase = 'C:\\Users\\Owner\\Desktop\\Tyler\\OneDrive\\Projects\\Movies\\Movie BI';
const reportDef = join(projectBase, 'Movie Dashboard.Report', 'definition');
const pagesDir = join(reportDef, 'pages');
const NEW_PAGE = 'pgWatchHabits';

const PAGES = {
  movies:      '2cec21eda0ac65e6e68a',
  watchlist:   '99a63aea31c93ab69180',
  actors:      '6f2e7727d8c1fe825b8d',
  directors:   'babb45a69dd6057916c0',
  genres:      'b3b2cb582bda2eab6245',
  series:      '8903f4a4a736ed69cd4b',
  actorCard:   'edd5072c72071f505ff9',
  watchHabits: NEW_PAGE,
};

const SCHEMA_VISUAL = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.10.0/schema.json';

// ── Helpers ──────────────────────────────────────────────────────────────────

function colRef(entity, property) {
  return { Column: { Expression: { SourceRef: { Entity: entity } }, Property: property } };
}

function proj(field, queryRef, nativeQueryRef, displayName) {
  const p = { field, queryRef, nativeQueryRef };
  if (displayName) p.displayName = displayName;
  return p;
}

function standardVco() {
  return {
    stylePreset: [{ properties: { name: { expr: { Literal: { Value: "'BoldHeader'" } } } } }],
    visualHeader: [{ properties: {
      show:       { expr: { Literal: { Value: 'false' } } },
      background: { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
      border:     { solid: { color: { expr: { Literal: { Value: "'#000000'" } } } } },
      foreground: { solid: { color: { expr: { Literal: { Value: "'#000000'" } } } } },
    } }],
    title: [{ properties: { titleWrap: { expr: { Literal: { Value: 'true' } } } } }],
    background: [{ properties: {
      show:         { expr: { Literal: { Value: 'true' } } },
      color:        { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
      transparency: { expr: { Literal: { Value: '100D' } } },
    } }],
    visualTooltip: [{ properties: {
      titleFontColor:       { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
      valueFontColor:       { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
      background:           { solid: { color: { expr: { Literal: { Value: "'#31394C'" } } } } },
      actionFontColor:      { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
      themedTitleFontColor: { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
      themedValueFontColor: { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
    } }],
    visualHeaderTooltip: [{ properties: {
      themedTitleFontColor: { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
    } }],
  };
}

function makeNavButton(name, label, y, z, tabOrder, targetPage, isActive) {
  const fillArr = [
    { properties: { show: { expr: { Literal: { Value: 'false' } } } } },
    { properties: {
        fillColor:    { solid: { color: { expr: { Literal: { Value: "'#018DA2'" } } } } },
        transparency: { expr: { Literal: { Value: '50D' } } },
      }, selector: { id: 'hover' } },
  ];
  if (isActive) {
    fillArr.push({ properties: {
      fillColor:    { solid: { color: { expr: { Literal: { Value: "'#018DA2'" } } } } },
      transparency: { expr: { Literal: { Value: '95D' } } },
    }, selector: { id: 'default' } });
  }

  const textDefaultProps = {
    text:               { expr: { Literal: { Value: `'${label}'` } } },
    fontSize:           { expr: { Literal: { Value: '24D' } } },
    horizontalAlignment:{ expr: { Literal: { Value: "'left'" } } },
    leftMargin:         { expr: { Literal: { Value: '13L' } } },
    topMargin:          { expr: { Literal: { Value: '8L' } } },
    bottomMargin:       { expr: { Literal: { Value: '8L' } } },
  };
  if (isActive) {
    textDefaultProps.fontColor = { solid: { color: { expr: { Literal: { Value: "'#018DA2'" } } } } };
    textDefaultProps.bold = { expr: { Literal: { Value: 'false' } } };
  }

  const vco = {
    lockAspect: [{ properties: { show: { expr: { Literal: { Value: 'true' } } } } }],
    border:     [{ properties: { show: { expr: { Literal: { Value: 'false' } } } } }],
    title:      [{ properties: { titleWrap: { expr: { Literal: { Value: 'true' } } } } }],
    background: [{ properties: {
      show:         { expr: { Literal: { Value: 'false' } } },
      color:        { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
      transparency: { expr: { Literal: { Value: '100D' } } },
    } }],
    visualTooltip: [{ properties: {
      titleFontColor:       { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
      valueFontColor:       { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
      background:           { solid: { color: { expr: { Literal: { Value: "'#31394C'" } } } } },
      actionFontColor:      { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
      themedTitleFontColor: { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
      themedValueFontColor: { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
    } }],
    visualHeader: [{ properties: {
      show:       { expr: { Literal: { Value: 'false' } } },
      background: { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
      border:     { solid: { color: { expr: { Literal: { Value: "'#000000'" } } } } },
      foreground: { solid: { color: { expr: { Literal: { Value: "'#000000'" } } } } },
    } }],
    visualHeaderTooltip: [{ properties: {
      themedTitleFontColor: { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
    } }],
  };

  if (targetPage) {
    vco.visualLink = [{ properties: {
      show:               { expr: { Literal: { Value: 'true' } } },
      type:               { expr: { Literal: { Value: "'PageNavigation'" } } },
      navigationSection:  { expr: { Literal: { Value: `'${targetPage}'` } } },
      showDefaultTooltip: { expr: { Literal: { Value: 'false' } } },
    } }];
  }

  return {
    $schema: SCHEMA_VISUAL,
    name,
    position: { x: 1.0781671159029649, y, z, height: 75, width: 297.57412398921832, tabOrder },
    visual: {
      visualType: 'actionButton',
      objects: {
        icon:    [{ properties: { shapeType: { expr: { Literal: { Value: "'blank'" } } } }, selector: { id: 'default' } }],
        text:    [
          { properties: { show: { expr: { Literal: { Value: 'true' } } } } },
          { properties: textDefaultProps, selector: { id: 'default' } },
          { properties: {
              fontSize:  { expr: { Literal: { Value: '24D' } } },
              fontColor: { solid: { color: { expr: { Literal: { Value: "'#018DA2'" } } } } },
            }, selector: { id: 'hover' } },
        ],
        outline: [{ properties: { show: { expr: { Literal: { Value: 'false' } } } } }],
        fill:    fillArr,
      },
      visualContainerObjects: vco,
      drillFilterOtherVisuals: true,
    },
    howCreated: 'InsertVisualButton',
  };
}

// ── 1. Create page folder ─────────────────────────────────────────────────────
const pageDir   = join(pagesDir, NEW_PAGE);
const visualsDir = join(pageDir, 'visuals');
mkdirSync(visualsDir, { recursive: true });

// ── 2. page.json ──────────────────────────────────────────────────────────────
writeFileSync(join(pageDir, 'page.json'), JSON.stringify({
  $schema: 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json',
  name: NEW_PAGE,
  displayName: 'Watch Habits',
  displayOption: 'FitToPage',
  height: 900,
  width: 1600,
  visibility: 'HiddenInViewMode',
}, null, 2), 'utf8');
console.log('✔ page.json');

// ── 3. Sidebar shape ──────────────────────────────────────────────────────────
const sidebarShape = {
  $schema: SCHEMA_VISUAL,
  name: 'v00SidebarShape',
  position: { x: 0, y: 0, z: 0, height: 880, width: 299.99999999999994, tabOrder: 7000 },
  visual: {
    visualType: 'shape',
    objects: {
      shape:    [{ properties: { tileShape: { expr: { Literal: { Value: "'rectangle'" } } } } }],
      rotation: [{ properties: { shapeAngle: { expr: { Literal: { Value: '0L' } } } } }],
      outline:  [{ properties: { lineColor: { solid: { color: { expr: { Literal: { Value: "'#018DA2'" } } } } } }, selector: { id: 'default' } }],
      fill:     [{ properties: { show: { expr: { Literal: { Value: 'false' } } } } }],
      text: [
        { properties: { show: { expr: { Literal: { Value: 'true' } } } } },
        { properties: {
            verticalAlignment:   { expr: { Literal: { Value: "'top'" } } },
            text:                { expr: { Literal: { Value: "'Tyler''s Movie Dashboard'" } } },
            fontColor:           { solid: { color: { expr: { Literal: { Value: "'#018DA2'" } } } } },
            fontSize:            { expr: { Literal: { Value: '40D' } } },
            topMargin:           { expr: { Literal: { Value: '25L' } } },
            leftMargin:          { expr: { Literal: { Value: '13L' } } },
            rightMargin:         { expr: { Literal: { Value: '13L' } } },
            bottomMargin:        { expr: { Literal: { Value: '0L' } } },
            fontFamily:          { expr: { Literal: { Value: "'''Segoe UI Bold'', wf_segoe-ui_bold, helvetica, arial, sans-serif'" } } },
            horizontalAlignment: { expr: { Literal: { Value: "'left'" } } },
          }, selector: { id: 'default' } },
      ],
    },
    visualContainerObjects: { lockAspect: [{ properties: { show: { expr: { Literal: { Value: 'true' } } } } }] },
    drillFilterOtherVisuals: true,
  },
  howCreated: 'InsertVisualButton',
};

mkdirSync(join(visualsDir, 'v00SidebarShape'), { recursive: true });
writeFileSync(join(visualsDir, 'v00SidebarShape', 'visual.json'), JSON.stringify(sidebarShape, null, 2), 'utf8');
console.log('✔ v00SidebarShape');

// ── 4. Nav buttons on Watch Habits page ───────────────────────────────────────
// 8 buttons, starting at y=266.3, step=74.4 (matching existing pages)
const navDefs = [
  { name: 'v_nav_Movies',      label: 'Movies',       target: PAGES.movies,    isActive: false, y: 266.3,  z: 1000, to: 0    },
  { name: 'v_nav_WatchHabits', label: 'Watch Habits', target: null,            isActive: true,  y: 340.7,  z: 2000, to: 1000 },
  { name: 'v_nav_Watchlist',   label: 'Watchlist',    target: PAGES.watchlist, isActive: false, y: 415.1,  z: 3000, to: 2000 },
  { name: 'v_nav_Actors',      label: 'Actors',       target: PAGES.actors,    isActive: false, y: 489.5,  z: 4000, to: 3000 },
  { name: 'v_nav_Directors',   label: 'Directors',    target: PAGES.directors, isActive: false, y: 563.9,  z: 5000, to: 4000 },
  { name: 'v_nav_Genres',      label: 'Genres',       target: PAGES.genres,    isActive: false, y: 638.3,  z: 6000, to: 5000 },
  { name: 'v_nav_Series',      label: 'Series',       target: PAGES.series,    isActive: false, y: 712.7,  z: 7000, to: 6000 },
  { name: 'v_nav_ActorCard',   label: 'Actor Card',   target: PAGES.actorCard, isActive: false, y: 787.1,  z: 8000, to: 7000 },
];

for (const d of navDefs) {
  const btn = makeNavButton(d.name, d.label, d.y, d.z, d.to, d.target, d.isActive);
  const dir = join(visualsDir, d.name);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'visual.json'), JSON.stringify(btn, null, 2), 'utf8');
  console.log(`✔ nav/${d.name}`);
}

// ── 5. Content visuals ────────────────────────────────────────────────────────

// v01DonutLocation  –  Where do you watch? (count by Watch Location)
const v01DonutLocation = {
  $schema: SCHEMA_VISUAL,
  name: 'v01DonutLocation',
  position: { x: 320, y: 40, z: 1000, width: 390, height: 380, tabOrder: 100 },
  visual: {
    visualType: 'donutChart',
    query: {
      queryState: {
        Category: { projections: [proj(colRef('Movie Rankings', 'Watch Location'), 'Movie Rankings.Watch Location', 'Watch Location')] },
        Y:        { projections: [proj(colRef('Movie Rankings', 'Movie'), 'Count(Movie Rankings.Movie)', '# Movies', '# Movies')] },
      },
      sortDefinition: { sort: [{ field: colRef('Movie Rankings', 'Movie'), direction: 'Descending' }] },
    },
    objects: {},
    visualContainerObjects: standardVco(),
    drillFilterOtherVisuals: true,
  },
};

// v02BarWatchedWith  –  Avg score by viewing companion
const v02BarWatchedWith = {
  $schema: SCHEMA_VISUAL,
  name: 'v02BarWatchedWith',
  position: { x: 728, y: 40, z: 2000, width: 430, height: 380, tabOrder: 200 },
  visual: {
    visualType: 'clusteredBarChart',
    query: {
      queryState: {
        Category: { projections: [proj(colRef('Movie Rankings', 'Watched With'), 'Movie Rankings.Watched With', 'Watched With')] },
        Y:        { projections: [proj(colRef('Movie Rankings', 'Score'), 'Average(Movie Rankings.Score)', 'Avg Score', 'Avg Score')] },
      },
      sortDefinition: { sort: [{ field: colRef('Movie Rankings', 'Score'), direction: 'Descending' }] },
    },
    objects: {},
    visualContainerObjects: standardVco(),
    drillFilterOtherVisuals: true,
  },
};

// v03BarRewatched  –  Top rewatched movies (Times Watched)
const v03BarRewatched = {
  $schema: SCHEMA_VISUAL,
  name: 'v03BarRewatched',
  position: { x: 1176, y: 40, z: 3000, width: 394, height: 380, tabOrder: 300 },
  visual: {
    visualType: 'clusteredBarChart',
    query: {
      queryState: {
        Category: { projections: [proj(colRef('Movie Rankings', 'Movie'), 'Movie Rankings.Movie', 'Movie')] },
        Y:        { projections: [proj(colRef('Movie Rankings', 'Times Watched'), 'Sum(Movie Rankings.Times Watched)', 'Times Watched', 'Times Watched')] },
      },
      sortDefinition: { sort: [{ field: colRef('Movie Rankings', 'Times Watched'), direction: 'Descending' }] },
    },
    objects: {},
    visualContainerObjects: standardVco(),
    drillFilterOtherVisuals: true,
  },
};

// v04BarLanguage  –  Movies by language (how international is your taste?)
const v04BarLanguage = {
  $schema: SCHEMA_VISUAL,
  name: 'v04BarLanguage',
  position: { x: 320, y: 445, z: 4000, width: 540, height: 415, tabOrder: 400 },
  visual: {
    visualType: 'clusteredBarChart',
    query: {
      queryState: {
        Category: { projections: [proj(colRef('Movie Rankings', 'Language'), 'Movie Rankings.Language', 'Language')] },
        Y:        { projections: [proj(colRef('Movie Rankings', 'Movie'), 'Count(Movie Rankings.Movie)', '# Movies', '# Movies')] },
      },
      sortDefinition: { sort: [{ field: colRef('Movie Rankings', 'Movie'), direction: 'Descending' }] },
    },
    objects: {},
    visualContainerObjects: standardVco(),
    drillFilterOtherVisuals: true,
  },
};

// v05ColumnYear  –  Movies watched by release year (what era of cinema do you prefer?)
const v05ColumnYear = {
  $schema: SCHEMA_VISUAL,
  name: 'v05ColumnYear',
  position: { x: 878, y: 445, z: 5000, width: 692, height: 415, tabOrder: 500 },
  visual: {
    visualType: 'clusteredColumnChart',
    query: {
      queryState: {
        Category: { projections: [proj(colRef('Movie Rankings', 'Year'), 'Movie Rankings.Year', 'Year')] },
        Y:        { projections: [proj(colRef('Movie Rankings', 'Movie'), 'Count(Movie Rankings.Movie)', '# Movies', '# Movies')] },
      },
      sortDefinition: { sort: [{ field: colRef('Movie Rankings', 'Year'), direction: 'Ascending' }] },
    },
    objects: {},
    visualContainerObjects: standardVco(),
    drillFilterOtherVisuals: true,
  },
};

const contentVisuals = [v01DonutLocation, v02BarWatchedWith, v03BarRewatched, v04BarLanguage, v05ColumnYear];
for (const v of contentVisuals) {
  const dir = join(visualsDir, v.name);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'visual.json'), JSON.stringify(v, null, 2), 'utf8');
  console.log(`✔ content/${v.name}`);
}

// ── 6. Add "Watch Habits" button to all existing pages ───────────────────────
// Placed at y=787.1 (8th slot, below existing Actor Card at y=712.7)
const existingPageIds = [
  PAGES.movies, PAGES.watchlist, PAGES.actors, PAGES.directors,
  PAGES.genres, PAGES.series, PAGES.actorCard,
];

for (const pageId of existingPageIds) {
  const btn = makeNavButton('v_nav_WatchHabitsNew', 'Watch Habits', 787.1, 8000, 7000, NEW_PAGE, false);
  const dir = join(pagesDir, pageId, 'visuals', 'v_nav_WatchHabitsNew');
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'visual.json'), JSON.stringify(btn, null, 2), 'utf8');
  console.log(`✔ added Watch Habits btn → ${pageId}`);
}

// ── 7. Update pages.json ──────────────────────────────────────────────────────
const pagesJsonPath = join(pagesDir, 'pages.json');
const pagesJson = JSON.parse(readFileSync(pagesJsonPath, 'utf8'));

if (!pagesJson.pageOrder.includes(NEW_PAGE)) {
  pagesJson.pageOrder.splice(1, 0, NEW_PAGE);  // insert after Movie Dashboard
}

writeFileSync(pagesJsonPath, JSON.stringify(pagesJson, null, 2), 'utf8');
console.log('✔ pages.json updated');

console.log('\n✅  Watch Habits page created!');
console.log('   → Close Power BI Desktop if open, then reopen Movie Dashboard.pbip');
