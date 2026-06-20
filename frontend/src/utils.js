/**
 * Converts a raw outlet key like "the-wall-street-journal" into
 * a display name like "The Wall Street Journal".
 */
const OUTLET_DISPLAY_NAMES = {
  'cnn':                      'CNN',
  'bbc-news':                 'BBC News',
  'fox-news':                 'Fox News',
  'npr':                      'NPR',
  'politico':                 'Politico',
  'the-guardian':             'The Guardian',
  'abc-news':                 'ABC News',
  'reuters':                  'Reuters',
  'associated-press':         'Associated Press',
  'the-wall-street-journal':  'The Wall Street Journal',
  'the-new-york-times':       'The New York Times',
  'washington-post':          'Washington Post',
}

export function formatOutletName(key) {
  if (!key) return ''
  if (OUTLET_DISPLAY_NAMES[key]) return OUTLET_DISPLAY_NAMES[key]
  // Fallback: capitalise each word and replace dashes with spaces
  return key
    .split('-')
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}
