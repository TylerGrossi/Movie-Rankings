/**
 * fix-watch-habits-v3.mjs
 *
 * Fixes:
 *  1. Nav order on Watch Habits page — moves Watch Habits button LAST (position 8)
 *  2. Replaces content visuals:
 *       v01 = Watch Location (count, donut)
 *       v02 = Avg Score by Watch Location (bar + Avg reference line)
 *       v03 = Who You Watch With (count, bar)
 *       v04 = Avg Score by Watched With (bar + Avg reference line)
 *       v05 = Score Trend over time (combo: columns=count, line=avg score)
 *  3. Ensures all 7 existing pages have the Watch Habits button at y=787.1 (LAST)
 */

import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const BASE    = 'C:\\Users\\Owner\\Desktop\\Tyler\\OneDrive\\Projects\\Movies\\Movie BI';
const PAGES   = join(BASE, 'Movie Dashboard.Report', 'definition', 'pages');
const WH_PAGE = join(PAGES, 'pgWatchHabits');
const WH_VIS  = join(WH_PAGE, 'visuals');
const SCHEMA  = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.10.0/schema.json';

const PAGE_IDS = {
  movies:     '2cec21eda0ac65e6e68a',
  watchlist:  '99a63aea31c93ab69180',
  actors:     '6f2e7727d8c1fe825b8d',
  directors:  'babb45a69dd6057916c0',
  genres:     'b3b2cb582bda2eab6245',
  series:     '8903f4a4a736ed69cd4b',
  actorCard:  'edd5072c72071f505ff9',
  watchHabits: 'pgWatchHabits',
};

// ── helpers ───────────────────────────────────────────────────────────────────

function w(path, json) {
  mkdirSync(join(...path.split('/').slice(0, -1).map(p => p)), { recursive: true });
  writeFileSync(path, JSON.stringify(json, null, 2), 'utf8');
}

function save(dir, name, json) {
  const d = join(dir, name);
  mkdirSync(d, { recursive: true });
  writeFileSync(join(d, 'visual.json'), JSON.stringify(json, null, 2), 'utf8');
  console.log(`  ✔ ${name}`);
}

function catProj(entity, property) {
  return {
    field: { Column: { Expression: { SourceRef: { Entity: entity } }, Property: property } },
    queryRef: `${entity}.${property}`,
    nativeQueryRef: property,
    active: true,
  };
}

// fn: 0=Sum, 1=Avg, 2=CountNonNull, 3=Min, 4=Max
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
  return {
    Aggregation: {
      Expression: { Column: { Expression: { SourceRef: { Entity: entity } }, Property: property } },
      Function: fn,
    },
  };
}

function colField(entity, property) {
  return { Column: { Expression: { SourceRef: { Entity: entity } }, Property: property } };
}

function lit(v) { return { expr: { Literal: { Value: v } } }; }
function color(hex) { return { solid: { color: lit(`'${hex}'`) } }; }
function measureRef(entity, property) {
  return { expr: { Measure: { Expression: { SourceRef: { Entity: entity } }, Property: property } } };
}

// Standard chart visualContainerObjects — no stylePreset, matches existing pages
function chartVco(title) {
  return {
    title: [{ properties: {
      text:      lit(`'${title}'`),
      titleWrap: lit('true'),
      alignment: lit("'center'"),
      fontSize:  lit('14D'),
    } }],
    visualHeader: [{ properties: { show: lit('false') } }],
    background: [{ properties: {
      show:         lit('true'),
      color:        color('#FFFFFF'),
      transparency: lit('100D'),
    } }],
    visualTooltip: [{ properties: {
      titleFontColor:       color('#FFFFFF'),
      valueFontColor:       color('#FFFFFF'),
      background:           color('#31394C'),
      actionFontColor:      color('#FFFFFF'),
      themedTitleFontColor: color('#FFFFFF'),
      themedValueFontColor: color('#FFFFFF'),
    } }],
    visualHeaderTooltip: [{ properties: { themedTitleFontColor: color('#FFFFFF') } }],
    padding: [{ properties: {
      top: lit('5D'), bottom: lit('0D'), left: lit('5D'), right: lit('0D'),
    } }],
  };
}

// Standard axis/label objects for horizontal bar charts
function hBarObjects() {
  return {
    labels: [{ properties: {
      show:          lit('true'),
      labelPosition: lit("'OutsideEnd'"),
      labelDensity:  lit('100L'),
      optimizeLabelDisplay:   lit('false'),
      labelContainerMaxWidth: lit('199D'),
      fontSize:      lit('9D'),
    } }],
    categoryAxis: [{ properties: {
      preferredCategoryWidth: lit('20D'),
      maxMarginFactor:        lit('50L'),
      concatenateLabels:      lit('true'),
      fontSize:               lit('9D'),
      showAxisTitle:          lit('false'),
    } }],
    valueAxis: [{ properties: {
      fontSize:      lit('9D'),
      showAxisTitle: lit('false'),
    } }],
  };
}

// Avg reference line using the existing Movie Rankings[Avg] measure
function avgRefLine(color = '#018DA2') {
  return [{
    properties: {
      show:           lit('true'),
      displayName:    lit("'Avg'"),
      value:          measureRef('Movie Rankings', 'Avg'),
      style:          lit("'dotted'"),
      position:       lit("'back'"),
      width:          lit('1D'),
      transparency:   lit('0D'),
      lineColor:      { solid: { color: { expr: { Literal: { Value: `'${color}'` } } } } },
      dataLabelShow:  lit('true'),
      dataLabelColor: { solid: { color: { expr: { Literal: { Value: `'${color}'` } } } } },
      dataLabelDecimalPoints: lit('1D'),
    },
    selector: { id: '1' },
  }];
}

// ─────────────────────────────────────────────────────────────────────────────
//  NAV BUTTON BUILDER
// ─────────────────────────────────────────────────────────────────────────────

function navButton(name, label, y, z, tabOrder, targetPage, isActive) {
  const fillArr = [
    { properties: { show: lit('false') } },
    { properties: {
        fillColor:    color('#018DA2'),
        transparency: lit('50D'),
      }, selector: { id: 'hover' } },
  ];
  if (isActive) {
    fillArr.push({ properties: {
      fillColor:    color('#018DA2'),
      transparency: lit('95D'),
    }, selector: { id: 'default' } });
  }

  const defaultTextProps = {
    text:               lit(`'${label}'`),
    fontSize:           lit('24D'),
    horizontalAlignment:lit("'left'"),
    leftMargin:         lit('13L'),
    topMargin:          lit('8L'),
    bottomMargin:       lit('8L'),
  };
  if (isActive) {
    defaultTextProps.fontColor = color('#018DA2');
    defaultTextProps.bold = lit('false');
  }

  const vco = {
    lockAspect:  [{ properties: { show: lit('true') } }],
    border:      [{ properties: { show: lit('false') } }],
    title:       [{ properties: { titleWrap: lit('true') } }],
    background:  [{ properties: { show: lit('false'), color: color('#FFFFFF'), transparency: lit('100D') } }],
    visualTooltip: [{ properties: {
      titleFontColor: color('#FFFFFF'), valueFontColor: color('#FFFFFF'),
      background: color('#31394C'), actionFontColor: color('#FFFFFF'),
      themedTitleFontColor: color('#FFFFFF'), themedValueFontColor: color('#FFFFFF'),
    } }],
    visualHeader: [{ properties: {
      show: lit('false'), background: color('#FFFFFF'),
      border: color('#000000'), foreground: color('#000000'),
    } }],
    visualHeaderTooltip: [{ properties: { themedTitleFontColor: color('#FFFFFF') } }],
  };

  if (targetPage) {
    vco.visualLink = [{ properties: {
      show:               lit('true'),
      type:               lit("'PageNavigation'"),
      navigationSection:  lit(`'${targetPage}'`),
      showDefaultTooltip: lit('false'),
    } }];
  }

  return {
    $schema: SCHEMA,
    name,
    position: { x: 1.0781671159029649, y, z, height: 75, width: 297.57412398921832, tabOrder },
    visual: {
      visualType: 'actionButton',
      objects: {
        icon:    [{ properties: { shapeType: lit("'blank'") }, selector: { id: 'default' } }],
        text:    [
          { properties: { show: lit('true') } },
          { properties: defaultTextProps, selector: { id: 'default' } },
          { properties: { fontSize: lit('24D'), fontColor: color('#018DA2') }, selector: { id: 'hover' } },
        ],
        outline: [{ properties: { show: lit('false') } }],
        fill:    fillArr,
      },
      visualContainerObjects: vco,
      drillFilterOtherVisuals: true,
    },
    howCreated: 'InsertVisualButton',
  };
}

// ═════════════════════════════════════════════════════════════════════════════
//  PART 1 — Fix nav button order on Watch Habits page (Watch Habits LAST)
// ═════════════════════════════════════════════════════════════════════════════

console.log('\n── Part 1: Fix Watch Habits page nav (Watch Habits → last) ──');

// New correct order: Movies, Watchlist, Actors, Directors, Genres, Series, Actor Card, Watch Habits
const watchHabitsNav = [
  { name: 'v_nav_Movies',      label: 'Movies',       y: 266.3, z: 1000, to: 0,    target: PAGE_IDS.movies,      active: false },
  { name: 'v_nav_Watchlist',   label: 'Watchlist',    y: 340.7, z: 2000, to: 1000, target: PAGE_IDS.watchlist,   active: false },
  { name: 'v_nav_Actors',      label: 'Actors',       y: 415.1, z: 3000, to: 2000, target: PAGE_IDS.actors,      active: false },
  { name: 'v_nav_Directors',   label: 'Directors',    y: 489.5, z: 4000, to: 3000, target: PAGE_IDS.directors,   active: false },
  { name: 'v_nav_Genres',      label: 'Genres',       y: 563.9, z: 5000, to: 4000, target: PAGE_IDS.genres,      active: false },
  { name: 'v_nav_Series',      label: 'Series',       y: 638.3, z: 6000, to: 5000, target: PAGE_IDS.series,      active: false },
  { name: 'v_nav_ActorCard',   label: 'Actor Card',   y: 712.7, z: 7000, to: 6000, target: PAGE_IDS.actorCard,   active: false },
  { name: 'v_nav_WatchHabits', label: 'Watch Habits', y: 787.1, z: 8000, to: 7000, target: null,                 active: true  },
];

for (const b of watchHabitsNav) {
  save(WH_VIS, b.name, navButton(b.name, b.label, b.y, b.z, b.to, b.target, b.active));
}

// ═════════════════════════════════════════════════════════════════════════════
//  PART 2 — Ensure all existing pages have Watch Habits button (LAST, y=787.1)
// ═════════════════════════════════════════════════════════════════════════════

console.log('\n── Part 2: Ensure Watch Habits button on all 7 existing pages ──');

const existingPages = [
  PAGE_IDS.movies, PAGE_IDS.watchlist, PAGE_IDS.actors, PAGE_IDS.directors,
  PAGE_IDS.genres, PAGE_IDS.series, PAGE_IDS.actorCard,
];

for (const pageId of existingPages) {
  const btn = navButton('v_nav_WatchHabitsNew', 'Watch Habits', 787.1, 8000, 7000, PAGE_IDS.watchHabits, false);
  save(join(PAGES, pageId, 'visuals'), 'v_nav_WatchHabitsNew', btn);
}

// ═════════════════════════════════════════════════════════════════════════════
//  PART 3 — Replace content visuals with score-focused charts
// ═════════════════════════════════════════════════════════════════════════════

console.log('\n── Part 3: Rewrite content visuals ──');

// Layout (1600×900, sidebar 0-300px, content 320-1580px):
//
// Row 1 (y=30, h=390):
//   v01 Watch Location donut         x=320   w=375
//   v02 Avg Score by Watch Location  x=710   w=420   [was v03BarRewatched folder]
//   v03 Who You Watch With count     x=1145  w=425   [was v02BarWatchedWith folder]
//
// Row 2 (y=440, h=430):
//   v04 Avg Score by Watched With    x=320   w=530   [was v04BarLanguage folder]
//   v05 Score Trend (combo)          x=865   w=705   [was v05ColumnYear folder]

// ── v01DonutLocation — Watch Location: count of movies ───────────────────────
save(WH_VIS, 'v01DonutLocation', {
  $schema: SCHEMA,
  name: 'v01DonutLocation',
  position: { x: 320, y: 30, z: 1000, width: 375, height: 390, tabOrder: 100 },
  visual: {
    visualType: 'donutChart',
    query: {
      queryState: {
        Category: { projections: [catProj('Movie Rankings', 'Watch Location')] },
        Y: { projections: [aggProj('Movie Rankings', 'Movie', 2,
               'CountNonNull(Movie Rankings.Movie)', '# Movies', '# Movies')] },
      },
      sortDefinition: {
        sort: [{ field: aggField('Movie Rankings', 'Movie', 2), direction: 'Descending' }],
        isDefaultSort: true,
      },
    },
    objects: {
      legend: [{ properties: {
        show:     lit('true'),
        position: lit("'Right'"),
        fontSize: lit('10D'),
      } }],
      labels: [{ properties: { show: lit('true'), fontSize: lit('10D') } }],
    },
    visualContainerObjects: chartVco('Watch Location'),
    drillFilterOtherVisuals: true,
  },
});

// ── v03BarRewatched (folder) → Avg Score by Watch Location ───────────────────
save(WH_VIS, 'v03BarRewatched', {
  $schema: SCHEMA,
  name: 'v03AvgScoreByLocation',
  position: { x: 710, y: 30, z: 2000, width: 420, height: 390, tabOrder: 200 },
  visual: {
    visualType: 'clusteredBarChart',
    query: {
      queryState: {
        Category: { projections: [catProj('Movie Rankings', 'Watch Location')] },
        Y: { projections: [aggProj('Movie Rankings', 'Score', 1,
               'Average(Movie Rankings.Score)', 'Avg Score', 'Avg Score')] },
      },
      sortDefinition: {
        sort: [{ field: aggField('Movie Rankings', 'Score', 1), direction: 'Descending' }],
        isDefaultSort: true,
      },
    },
    objects: {
      ...hBarObjects(),
      y1AxisReferenceLine: avgRefLine('#018DA2'),
      valueAxis: [{ properties: {
        fontSize:      lit('9D'),
        showAxisTitle: lit('false'),
        start:         lit('0D'),
        end:           lit('11D'),
      } }],
    },
    visualContainerObjects: chartVco('Avg Score by Watch Location'),
    drillFilterOtherVisuals: true,
  },
});

// ── v02BarWatchedWith (folder) → Who You Watch With: count of movies ─────────
save(WH_VIS, 'v02BarWatchedWith', {
  $schema: SCHEMA,
  name: 'v02WatchedWithCount',
  position: { x: 1145, y: 30, z: 3000, width: 425, height: 390, tabOrder: 300 },
  visual: {
    visualType: 'clusteredBarChart',
    query: {
      queryState: {
        Category: { projections: [catProj('Movie Rankings', 'Watched With')] },
        Y: { projections: [aggProj('Movie Rankings', 'Movie', 2,
               'CountNonNull(Movie Rankings.Movie)', '# Movies', '# Movies')] },
      },
      sortDefinition: {
        sort: [{ field: aggField('Movie Rankings', 'Movie', 2), direction: 'Descending' }],
        isDefaultSort: true,
      },
    },
    objects: hBarObjects(),
    visualContainerObjects: chartVco('Who Do You Watch With?'),
    drillFilterOtherVisuals: true,
  },
});

// ── v04BarLanguage (folder) → Avg Score by Watched With ──────────────────────
save(WH_VIS, 'v04BarLanguage', {
  $schema: SCHEMA,
  name: 'v04AvgScoreByWatchedWith',
  position: { x: 320, y: 440, z: 4000, width: 530, height: 430, tabOrder: 400 },
  visual: {
    visualType: 'clusteredBarChart',
    query: {
      queryState: {
        Category: { projections: [catProj('Movie Rankings', 'Watched With')] },
        Y: { projections: [aggProj('Movie Rankings', 'Score', 1,
               'Average(Movie Rankings.Score)', 'Avg Score', 'Avg Score')] },
      },
      sortDefinition: {
        sort: [{ field: aggField('Movie Rankings', 'Score', 1), direction: 'Descending' }],
        isDefaultSort: true,
      },
    },
    objects: {
      ...hBarObjects(),
      y1AxisReferenceLine: avgRefLine('#018DA2'),
      valueAxis: [{ properties: {
        fontSize:      lit('9D'),
        showAxisTitle: lit('false'),
        start:         lit('0D'),
        end:           lit('11D'),
      } }],
      spacing: [{ properties: { verticalSpacing: lit('0D') } }],
    },
    visualContainerObjects: chartVco('Avg Score by Watched With'),
    drillFilterOtherVisuals: true,
  },
});

// ── v05ColumnYear (folder) → Score Trend over time (combo chart) ─────────────
// Columns = # movies watched per year, Line = avg score per year
save(WH_VIS, 'v05ColumnYear', {
  $schema: SCHEMA,
  name: 'v05ScoreTrend',
  position: { x: 865, y: 440, z: 5000, width: 705, height: 430, tabOrder: 500 },
  visual: {
    visualType: 'lineStackedColumnComboChart',
    query: {
      queryState: {
        Category: { projections: [catProj('Movie Rankings', 'Date Watched')] },
        ColumnY: { projections: [aggProj('Movie Rankings', 'Movie', 2,
                     'CountNonNull(Movie Rankings.Movie)', '# Movies', '# Movies')] },
        LineY: { projections: [aggProj('Movie Rankings', 'Score', 1,
                   'Average(Movie Rankings.Score)', 'Avg Score', 'Avg Score')] },
      },
      sortDefinition: {
        sort: [{ field: colField('Movie Rankings', 'Date Watched'), direction: 'Ascending' }],
      },
    },
    objects: {
      valueAxis: [{ properties: {
        secShow:          lit('false'),
        start:            lit('0D'),
        end:              lit('11D'),
        secStart:         lit('3D'),
        secEnd:           lit('10D'),
        secShowAxisTitle: lit('false'),
        fontSize:         lit('9D'),
        showAxisTitle:    lit('false'),
      } }],
      legend: [{ properties: {
        show:     lit('true'),
        position: lit("'TopRight'"),
        fontSize: lit('10D'),
      } }],
      categoryAxis: [{ properties: {
        fontSize:      lit('9D'),
        showAxisTitle: lit('false'),
      } }],
      labels: [{ properties: { show: lit('false') } }],
      // Avg reference line (red dotted) showing your all-time avg
      y1AxisReferenceLine: [{
        properties: {
          show:           lit('true'),
          displayName:    lit("'All-Time Avg'"),
          value:          measureRef('Movie Rankings', 'Avg'),
          style:          lit("'dotted'"),
          position:       lit("'back'"),
          width:          lit('1D'),
          transparency:   lit('0D'),
          lineColor:      color('#D34E59'),
          dataLabelShow:  lit('true'),
          dataLabelColor: color('#D34E59'),
          dataLabelDecimalPoints: lit('1D'),
        },
        selector: { id: '1' },
      }],
    },
    visualContainerObjects: {
      ...chartVco('Score & Movies Watched Over Time'),
      padding: [{ properties: {
        top: lit('20D'), right: lit('20D'), bottom: lit('20D'), left: lit('20D'),
      } }],
    },
    drillFilterOtherVisuals: true,
  },
});

console.log('\n✅  All fixes applied!');
console.log('   1. Watch Habits nav button is now LAST on the Watch Habits page');
console.log('   2. Watch Habits button confirmed on all 7 existing pages');
console.log('   3. Content visuals updated with score-focused charts');
console.log('\n   → Close Power BI Desktop, reopen Movie Dashboard.pbip');
