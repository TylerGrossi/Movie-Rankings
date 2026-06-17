/**
 * fix-watch-habits-v4.mjs
 *
 * Final comprehensive fix:
 *  1. Nav: Watch Habits LAST on Watch Habits page; button confirmed on all other pages
 *  2. Charts: fix combo (Y/Y2), use Movie_WatchedWith for split Watched With charts
 *  3. Layout: 3 charts top / 2 charts middle / 1 table bottom
 *  4. New table visual cross-filtering with charts
 */

import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const BASE   = 'C:\\Users\\Owner\\Desktop\\Tyler\\OneDrive\\Projects\\Movies\\Movie BI';
const PAGES  = join(BASE, 'Movie Dashboard.Report', 'definition', 'pages');
const WH_VIS = join(PAGES, 'pgWatchHabits', 'visuals');
const SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.10.0/schema.json';

const PID = {
  movies:      '2cec21eda0ac65e6e68a',
  watchlist:   '99a63aea31c93ab69180',
  actors:      '6f2e7727d8c1fe825b8d',
  directors:   'babb45a69dd6057916c0',
  genres:      'b3b2cb582bda2eab6245',
  series:      '8903f4a4a736ed69cd4b',
  actorCard:   'edd5072c72071f505ff9',
  watchHabits: 'pgWatchHabits',
};

// ── micro-helpers ─────────────────────────────────────────────────────────────
const lit  = v  => ({ expr: { Literal: { Value: v } } });
const col  = hex => ({ solid: { color: lit(`'${hex}'`) } });
const msr  = (e, p) => ({ expr: { Measure: { Expression: { SourceRef: { Entity: e } }, Property: p } } });

function save(dir, name, json) {
  const d = join(dir, name);
  mkdirSync(d, { recursive: true });
  writeFileSync(join(d, 'visual.json'), JSON.stringify(json, null, 2), 'utf8');
  console.log(`  ✔ ${name}`);
}

// Column reference (category role, active)
function catProj(entity, property) {
  return {
    field: { Column: { Expression: { SourceRef: { Entity: entity } }, Property: property } },
    queryRef: `${entity}.${property}`,
    nativeQueryRef: property,
    active: true,
  };
}

// Aggregation reference (value roles): fn 0=Sum, 1=Avg, 2=CountNonNull
function aggProj(entity, property, fn, queryRef, nativeRef, displayName) {
  const p = {
    field: {
      Aggregation: {
        Expression: { Column: { Expression: { SourceRef: { Entity: entity } }, Property: property } },
        Function: fn,
      },
    },
    queryRef,
    nativeQueryRef: nativeRef,
  };
  if (displayName) p.displayName = displayName;
  return p;
}
function aggField(entity, property, fn) {
  return { Aggregation: { Expression: { Column: { Expression: { SourceRef: { Entity: entity } }, Property: property } }, Function: fn } };
}
function colField(entity, property) {
  return { Column: { Expression: { SourceRef: { Entity: entity } }, Property: property } };
}

// Chart visualContainerObjects — no stylePreset
function chartVco(title, padTop = 5) {
  return {
    title: [{ properties: { text: lit(`'${title}'`), titleWrap: lit('true'), alignment: lit("'center'"), fontSize: lit('14D') } }],
    visualHeader:        [{ properties: { show: lit('false') } }],
    background:          [{ properties: { show: lit('true'), color: col('#FFFFFF'), transparency: lit('100D') } }],
    visualTooltip:       [{ properties: { titleFontColor: col('#FFFFFF'), valueFontColor: col('#FFFFFF'), background: col('#31394C'), actionFontColor: col('#FFFFFF'), themedTitleFontColor: col('#FFFFFF'), themedValueFontColor: col('#FFFFFF') } }],
    visualHeaderTooltip: [{ properties: { themedTitleFontColor: col('#FFFFFF') } }],
    padding:             [{ properties: { top: lit(`${padTop}D`), bottom: lit('0D'), left: lit('5D'), right: lit('0D') } }],
  };
}

// Bar chart axis/label objects
function barObjs() {
  return {
    labels:       [{ properties: { show: lit('true'), labelPosition: lit("'OutsideEnd'"), labelDensity: lit('100L'), optimizeLabelDisplay: lit('false'), labelContainerMaxWidth: lit('199D'), fontSize: lit('9D') } }],
    categoryAxis: [{ properties: { preferredCategoryWidth: lit('20D'), maxMarginFactor: lit('50L'), concatenateLabels: lit('true'), fontSize: lit('9D'), showAxisTitle: lit('false') } }],
    valueAxis:    [{ properties: { fontSize: lit('9D'), showAxisTitle: lit('false') } }],
  };
}

// Avg dotted reference line
function avgLine(hex = '#018DA2') {
  return [{
    properties: { show: lit('true'), displayName: lit("'Avg'"), value: msr('Movie Rankings', 'Avg'), style: lit("'dotted'"), position: lit("'back'"), width: lit('1D'), transparency: lit('0D'), lineColor: col(hex), dataLabelShow: lit('true'), dataLabelColor: col(hex), dataLabelDecimalPoints: lit('1D') },
    selector: { id: '1' },
  }];
}

// ─────────────────────────────────────────────────────────────────────────────
//  Table visual container objects — uses header, no stylePreset
// ─────────────────────────────────────────────────────────────────────────────
function tableVco() {
  return {
    visualHeader:        [{ properties: { show: lit('false') } }],
    background:          [{ properties: { show: lit('true'), color: col('#FFFFFF'), transparency: lit('100D') } }],
    visualTooltip:       [{ properties: { titleFontColor: col('#FFFFFF'), valueFontColor: col('#FFFFFF'), background: col('#31394C'), actionFontColor: col('#FFFFFF'), themedTitleFontColor: col('#FFFFFF'), themedValueFontColor: col('#FFFFFF') } }],
    visualHeaderTooltip: [{ properties: { themedTitleFontColor: col('#FFFFFF') } }],
    title:               [{ properties: { titleWrap: lit('true') } }],
  };
}

// ─────────────────────────────────────────────────────────────────────────────
//  NAV BUTTON BUILDER
// ─────────────────────────────────────────────────────────────────────────────
function navBtn(name, label, y, z, tabOrder, target, isActive) {
  const fill = [
    { properties: { show: lit('false') } },
    { properties: { fillColor: col('#018DA2'), transparency: lit('50D') }, selector: { id: 'hover' } },
  ];
  if (isActive) fill.push({ properties: { fillColor: col('#018DA2'), transparency: lit('95D') }, selector: { id: 'default' } });

  const defText = { text: lit(`'${label}'`), fontSize: lit('24D'), horizontalAlignment: lit("'left'"), leftMargin: lit('13L'), topMargin: lit('8L'), bottomMargin: lit('8L') };
  if (isActive) { defText.fontColor = col('#018DA2'); defText.bold = lit('false'); }

  const vco = {
    lockAspect:  [{ properties: { show: lit('true') } }],
    border:      [{ properties: { show: lit('false') } }],
    title:       [{ properties: { titleWrap: lit('true') } }],
    background:  [{ properties: { show: lit('false'), color: col('#FFFFFF'), transparency: lit('100D') } }],
    visualTooltip: [{ properties: { titleFontColor: col('#FFFFFF'), valueFontColor: col('#FFFFFF'), background: col('#31394C'), actionFontColor: col('#FFFFFF'), themedTitleFontColor: col('#FFFFFF'), themedValueFontColor: col('#FFFFFF') } }],
    visualHeader: [{ properties: { show: lit('false'), background: col('#FFFFFF'), border: col('#000000'), foreground: col('#000000') } }],
    visualHeaderTooltip: [{ properties: { themedTitleFontColor: col('#FFFFFF') } }],
  };
  if (target) {
    vco.visualLink = [{ properties: { show: lit('true'), type: lit("'PageNavigation'"), navigationSection: lit(`'${target}'`), showDefaultTooltip: lit('false') } }];
  }

  return {
    $schema: SCHEMA, name,
    position: { x: 1.0781671159029649, y, z, height: 75, width: 297.57412398921832, tabOrder },
    visual: {
      visualType: 'actionButton',
      objects: {
        icon:    [{ properties: { shapeType: lit("'blank'") }, selector: { id: 'default' } }],
        text:    [{ properties: { show: lit('true') } }, { properties: defText, selector: { id: 'default' } }, { properties: { fontSize: lit('24D'), fontColor: col('#018DA2') }, selector: { id: 'hover' } }],
        outline: [{ properties: { show: lit('false') } }],
        fill,
      },
      visualContainerObjects: vco,
      drillFilterOtherVisuals: true,
    },
    howCreated: 'InsertVisualButton',
  };
}

// ═════════════════════════════════════════════════════════════════════════════
//  PART 1 — Nav: Watch Habits LAST on Watch Habits page
// ═════════════════════════════════════════════════════════════════════════════
console.log('\n── Part 1: Nav buttons on Watch Habits page ──');
const whNav = [
  { name: 'v_nav_Movies',      label: 'Movies',       y: 266.3, z: 1000, to: 0,    target: PID.movies,     active: false },
  { name: 'v_nav_Watchlist',   label: 'Watchlist',    y: 340.7, z: 2000, to: 1000, target: PID.watchlist,  active: false },
  { name: 'v_nav_Actors',      label: 'Actors',       y: 415.1, z: 3000, to: 2000, target: PID.actors,     active: false },
  { name: 'v_nav_Directors',   label: 'Directors',    y: 489.5, z: 4000, to: 3000, target: PID.directors,  active: false },
  { name: 'v_nav_Genres',      label: 'Genres',       y: 563.9, z: 5000, to: 4000, target: PID.genres,     active: false },
  { name: 'v_nav_Series',      label: 'Series',       y: 638.3, z: 6000, to: 5000, target: PID.series,     active: false },
  { name: 'v_nav_ActorCard',   label: 'Actor Card',   y: 712.7, z: 7000, to: 6000, target: PID.actorCard,  active: false },
  { name: 'v_nav_WatchHabits', label: 'Watch Habits', y: 787.1, z: 8000, to: 7000, target: null,           active: true  },
];
for (const b of whNav) save(WH_VIS, b.name, navBtn(b.name, b.label, b.y, b.z, b.to, b.target, b.active));

// ═════════════════════════════════════════════════════════════════════════════
//  PART 2 — Watch Habits button on all 7 existing pages (y=787.1, LAST)
// ═════════════════════════════════════════════════════════════════════════════
console.log('\n── Part 2: Watch Habits button on all other pages ──');
for (const pid of [PID.movies, PID.watchlist, PID.actors, PID.directors, PID.genres, PID.series, PID.actorCard]) {
  save(join(PAGES, pid, 'visuals'), 'v_nav_WatchHabitsNew',
    navBtn('v_nav_WatchHabitsNew', 'Watch Habits', 787.1, 8000, 7000, PID.watchHabits, false));
}

// ═════════════════════════════════════════════════════════════════════════════
//  PART 3 — Content visuals (new compact layout + table)
// ═════════════════════════════════════════════════════════════════════════════
console.log('\n── Part 3: Content visuals ──');

// Layout (sidebar 0-299, content 320-1570):
//
// Row 1 y=30  h=255  — 3 charts
//   v01 Watch Location donut         x=320  w=375
//   v03 Avg Score by Watch Location  x=710  w=415
//   v02 Who Watched With (split)     x=1140 w=430
//
// Row 2 y=300 h=255  — 2 charts
//   v04 Avg Score by Watched With    x=320  w=530
//   v05 Score Trend combo            x=865  w=705
//
// Row 3 y=568 h=302  — table
//   v06 Movie detail table           x=320  w=1250

// ── v01 Watch Location donut ─────────────────────────────────────────────────
save(WH_VIS, 'v01DonutLocation', {
  $schema: SCHEMA, name: 'v01DonutLocation',
  position: { x: 320, y: 30, z: 1000, width: 375, height: 255, tabOrder: 100 },
  visual: {
    visualType: 'donutChart',
    query: {
      queryState: {
        Category: { projections: [catProj('Movie Rankings', 'Watch Location')] },
        Y:        { projections: [aggProj('Movie Rankings', 'Movie', 2, 'CountNonNull(Movie Rankings.Movie)', '# Movies', '# Movies')] },
      },
      sortDefinition: { sort: [{ field: aggField('Movie Rankings', 'Movie', 2), direction: 'Descending' }], isDefaultSort: true },
    },
    objects: {
      legend: [{ properties: { show: lit('true'), position: lit("'Right'"), fontSize: lit('9D') } }],
      labels: [{ properties: { show: lit('true'), fontSize: lit('9D') } }],
    },
    visualContainerObjects: chartVco('Watch Location'),
    drillFilterOtherVisuals: true,
  },
});

// ── v03BarRewatched folder → Avg Score by Watch Location ─────────────────────
save(WH_VIS, 'v03BarRewatched', {
  $schema: SCHEMA, name: 'v03AvgScoreByLocation',
  position: { x: 710, y: 30, z: 2000, width: 415, height: 255, tabOrder: 200 },
  visual: {
    visualType: 'clusteredBarChart',
    query: {
      queryState: {
        Category: { projections: [catProj('Movie Rankings', 'Watch Location')] },
        Y:        { projections: [aggProj('Movie Rankings', 'Score', 1, 'Average(Movie Rankings.Score)', 'Avg Score', 'Avg Score')] },
      },
      sortDefinition: { sort: [{ field: aggField('Movie Rankings', 'Score', 1), direction: 'Descending' }], isDefaultSort: true },
    },
    objects: {
      ...barObjs(),
      valueAxis: [{ properties: { fontSize: lit('9D'), showAxisTitle: lit('false'), start: lit('0D'), end: lit('11D') } }],
      y1AxisReferenceLine: avgLine('#018DA2'),
    },
    visualContainerObjects: chartVco('Avg Score by Watch Location'),
    drillFilterOtherVisuals: true,
  },
});

// ── v02BarWatchedWith folder → Who You Watch With (Movie_WatchedWith split) ───
save(WH_VIS, 'v02BarWatchedWith', {
  $schema: SCHEMA, name: 'v02WatchedWithCount',
  position: { x: 1140, y: 30, z: 3000, width: 430, height: 255, tabOrder: 300 },
  visual: {
    visualType: 'clusteredBarChart',
    query: {
      queryState: {
        // Uses Movie_WatchedWith table — each person is one row after comma-split
        Category: { projections: [catProj('Movie_WatchedWith', 'Watched With')] },
        Y:        { projections: [aggProj('Movie_WatchedWith', 'Movie', 2, 'CountNonNull(Movie_WatchedWith.Movie)', '# Movies', '# Movies')] },
      },
      sortDefinition: { sort: [{ field: aggField('Movie_WatchedWith', 'Movie', 2), direction: 'Descending' }], isDefaultSort: true },
    },
    objects: barObjs(),
    visualContainerObjects: chartVco('Who Do You Watch With?'),
    drillFilterOtherVisuals: true,
  },
});

// ── v04BarLanguage folder → Avg Score by Watched With (split) ────────────────
save(WH_VIS, 'v04BarLanguage', {
  $schema: SCHEMA, name: 'v04AvgScoreByWatchedWith',
  position: { x: 320, y: 300, z: 4000, width: 530, height: 255, tabOrder: 400 },
  visual: {
    visualType: 'clusteredBarChart',
    query: {
      queryState: {
        Category: { projections: [catProj('Movie_WatchedWith', 'Watched With')] },
        Y:        { projections: [aggProj('Movie_WatchedWith', 'Score', 1, 'Average(Movie_WatchedWith.Score)', 'Avg Score', 'Avg Score')] },
      },
      sortDefinition: { sort: [{ field: aggField('Movie_WatchedWith', 'Score', 1), direction: 'Descending' }], isDefaultSort: true },
    },
    objects: {
      ...barObjs(),
      valueAxis: [{ properties: { fontSize: lit('9D'), showAxisTitle: lit('false'), start: lit('0D'), end: lit('11D') } }],
      y1AxisReferenceLine: avgLine('#018DA2'),
      spacing: [{ properties: { verticalSpacing: lit('0D') } }],
    },
    visualContainerObjects: chartVco('Avg Score by Watched With'),
    drillFilterOtherVisuals: true,
  },
});

// ── v05ColumnYear folder → Score Trend over time (combo — FIXED: Y + Y2) ─────
save(WH_VIS, 'v05ColumnYear', {
  $schema: SCHEMA, name: 'v05ScoreTrend',
  position: { x: 865, y: 300, z: 5000, width: 705, height: 255, tabOrder: 500 },
  visual: {
    visualType: 'lineStackedColumnComboChart',
    query: {
      queryState: {
        Category: { projections: [catProj('Movie Rankings', 'Date Watched')] },
        // Y  = column bars (count of movies watched)
        Y:  { projections: [aggProj('Movie Rankings', 'Movie', 2, 'CountNonNull(Movie Rankings.Movie)', '# Movies', '# Movies')] },
        // Y2 = line (avg score)
        Y2: { projections: [aggProj('Movie Rankings', 'Score', 1, 'Average(Movie Rankings.Score)', 'Avg Score', 'Avg Score')] },
      },
      sortDefinition: { sort: [{ field: colField('Movie Rankings', 'Date Watched'), direction: 'Ascending' }] },
    },
    objects: {
      valueAxis: [{ properties: {
        secShow: lit('false'), start: lit('0D'), end: lit('11D'),
        secStart: lit('0D'), secEnd: lit('11D'), secShowAxisTitle: lit('false'),
        fontSize: lit('9D'), showAxisTitle: lit('false'),
      } }],
      legend:      [{ properties: { show: lit('true'), position: lit("'TopRight'"), fontSize: lit('10D') } }],
      categoryAxis:[{ properties: { fontSize: lit('9D'), showAxisTitle: lit('false') } }],
      labels:      [{ properties: { show: lit('false') } }],
      y1AxisReferenceLine: [{
        properties: { show: lit('true'), displayName: lit("'All-Time Avg'"), value: msr('Movie Rankings', 'Avg'), style: lit("'dotted'"), position: lit("'back'"), width: lit('1D'), transparency: lit('0D'), lineColor: col('#D34E59'), dataLabelShow: lit('true'), dataLabelColor: col('#D34E59'), dataLabelDecimalPoints: lit('1D') },
        selector: { id: '1' },
      }],
    },
    visualContainerObjects: {
      ...chartVco('Score & Movies Watched Over Time', 10),
      padding: [{ properties: { top: lit('10D'), right: lit('15D'), bottom: lit('5D'), left: lit('5D') } }],
    },
    drillFilterOtherVisuals: true,
  },
});

// ── v06Table — cross-filtering movie detail table ─────────────────────────────
save(WH_VIS, 'v06Table', {
  $schema: SCHEMA, name: 'v06MovieDetail',
  position: { x: 320, y: 568, z: 6000, width: 1250, height: 302, tabOrder: 600 },
  visual: {
    visualType: 'tableEx',
    query: {
      queryState: {
        Values: {
          projections: [
            { field: { Column: { Expression: { SourceRef: { Entity: 'Movie Rankings' } }, Property: 'Movie' } },         queryRef: 'Movie Rankings.Movie',         nativeQueryRef: 'Movie' },
            { field: { Aggregation: { Expression: { Column: { Expression: { SourceRef: { Entity: 'Movie Rankings' } }, Property: 'Score' } }, Function: 0 } }, queryRef: 'Sum(Movie Rankings.Score)', nativeQueryRef: 'Score' },
            { field: { Column: { Expression: { SourceRef: { Entity: 'Movie Rankings' } }, Property: 'Watch Location' } }, queryRef: 'Movie Rankings.Watch Location', nativeQueryRef: 'Watch Location' },
            { field: { Column: { Expression: { SourceRef: { Entity: 'Movie Rankings' } }, Property: 'Watched With' } },   queryRef: 'Movie Rankings.Watched With',   nativeQueryRef: 'Watched With' },
            { field: { Column: { Expression: { SourceRef: { Entity: 'Movie Rankings' } }, Property: 'Date Watched' } },   queryRef: 'Movie Rankings.Date Watched',   nativeQueryRef: 'Date Watched' },
            { field: { Column: { Expression: { SourceRef: { Entity: 'Movie Rankings' } }, Property: 'Director' } },       queryRef: 'Movie Rankings.Director',       nativeQueryRef: 'Director' },
            { field: { Column: { Expression: { SourceRef: { Entity: 'Movie Rankings' } }, Property: 'Year' } },           queryRef: 'Movie Rankings.Year',           nativeQueryRef: 'Year' },
            { field: { Aggregation: { Expression: { Column: { Expression: { SourceRef: { Entity: 'Movie Rankings' } }, Property: 'Times Watched' } }, Function: 0 } }, queryRef: 'Sum(Movie Rankings.Times Watched)', nativeQueryRef: 'Times Watched', displayName: 'Times Watched' },
          ],
        },
      },
      sortDefinition: { sort: [{ field: { Column: { Expression: { SourceRef: { Entity: 'Movie Rankings' } }, Property: 'Score' } }, direction: 'Descending' }] },
    },
    objects: {
      total: [{ properties: { totals: { expr: { Literal: { Value: 'false' } } } } }],
      columnHeaders: [{ properties: {
        autoSizeColumnWidth: lit('true'),
        fontSize:            lit('12D'),
        fontColor:           { solid: { color: { expr: { ThemeDataColor: { ColorId: 0, Percent: 0 } } } } },
        backColor:           col('#018da2'),
        columnAdjustment:    lit("'growToFit'"),
      } }],
      values: [{ properties: { fontSize: lit('11D') } }],
    },
    visualContainerObjects: tableVco(),
    drillFilterOtherVisuals: true,
  },
});

console.log('\n✅  All done!');
console.log('   IMPORTANT: Power BI Desktop must be fully closed, then:');
console.log('   1. Reopen Movie Dashboard.pbip');
console.log('   2. Power BI will detect the new Movie_WatchedWith table and load it');
console.log('   3. Navigate to Watch Habits to see the updated page');
console.log('   4. The "Who Do You Watch With?" and "Avg Score by Watched With" charts');
console.log('      now use the split table — Mom, Alexa, Dad will each be separate rows');
