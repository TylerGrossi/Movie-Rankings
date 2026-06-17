/**
 * fix-nav-group.mjs
 *
 * Adds `parentGroupName` to the v_nav_WatchHabitsNew button on every
 * existing page so it renders INSIDE the nav sidebar group — same as
 * every other nav button.
 *
 * Each page's visual group is at canvas y=10, so child positions are
 * group-relative.  The button y stays at 787.1 (group-relative), which
 * puts its canvas top at 10+787.1=797.1 — flush below Actor Card.
 */

import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const BASE  = 'C:\\Users\\Owner\\Desktop\\Tyler\\OneDrive\\Projects\\Movies\\Movie BI';
const PAGES = join(BASE, 'Movie Dashboard.Report', 'definition', 'pages');
const SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.10.0/schema.json';

// Each page folder ID → its nav-sidebar group folder name (parentGroupName)
const PAGES_MAP = [
  { pid: '2cec21eda0ac65e6e68a', group: '057e772621164b633005' }, // Movies
  { pid: '99a63aea31c93ab69180', group: 'd9638816b617c93a39a6' }, // Watchlist
  { pid: '6f2e7727d8c1fe825b8d', group: '900160b357d4aa7da164' }, // Actors
  { pid: 'babb45a69dd6057916c0', group: '5df1fd27aa41788b97a5' }, // Directors
  { pid: 'b3b2cb582bda2eab6245', group: 'e250e8fb157e6b9e893a' }, // Genres
  { pid: '8903f4a4a736ed69cd4b', group: '7f3f8c4a005d4573e081' }, // Series
  { pid: 'edd5072c72071f505ff9', group: '1371374080af0b8344bb' }, // Actor Card
];

const lit = v  => ({ expr: { Literal: { Value: v } } });
const col = hex => ({ solid: { color: lit(`'${hex}'`) } });

function navBtn(name, label, y, z, tabOrder, target, isActive, parentGroupName) {
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

  const obj = {
    $schema: SCHEMA, name,
    position: { x: 1.0781671159029649, y, z, height: 75, width: 297.57412398921832, tabOrder },
    visual: {
      visualType: 'actionButton',
      objects: {
        icon:    [{ properties: { shapeType: lit("'blank'") }, selector: { id: 'default' } }],
        text:    [
          { properties: { show: lit('true') } },
          { properties: defText, selector: { id: 'default' } },
          { properties: { fontSize: lit('24D'), fontColor: col('#018DA2') }, selector: { id: 'hover' } },
        ],
        outline: [{ properties: { show: lit('false') } }],
        fill,
      },
      visualContainerObjects: vco,
      drillFilterOtherVisuals: true,
    },
    parentGroupName,
    howCreated: 'InsertVisualButton',
  };
  return obj;
}

function save(dir, name, json) {
  const d = join(dir, name);
  mkdirSync(d, { recursive: true });
  writeFileSync(join(d, 'visual.json'), JSON.stringify(json, null, 2), 'utf8');
}

console.log('── Fixing v_nav_WatchHabitsNew on all 7 existing pages ──\n');

for (const { pid, group } of PAGES_MAP) {
  const visDir = join(PAGES, pid, 'visuals');
  // y=787.1 is group-relative (group is at canvas y=10)
  // → button canvas top = 10 + 787.1 = 797.1, right below Actor Card (canvas bottom ≈ 797.7)
  save(visDir, 'v_nav_WatchHabitsNew',
    navBtn('v_nav_WatchHabitsNew', 'Watch Habits', 787.1, 8000, 7000, 'pgWatchHabits', false, group));
  console.log(`  ✔ ${pid}  (group: ${group})`);
}

console.log('\n✅  Done — Watch Habits button is now inside the nav group on all pages.');
console.log('   Close Power BI Desktop fully, then reopen Movie Dashboard.pbip.');
