/**
 * Format company name for display - handles domain-style names
 * "oflahertyconstruction" -> "O'Flaherty Construction"
 * "acme-corp" -> "Acme Corp"
 * "mountedenplumbing" -> "Mount Eden Plumbing"
 */
export function formatCompanyName(name: string): string {
  if (!name) return ''

  // Remove common TLDs and www (handle compound TLDs like .co.uk, .com.au first)
  let cleaned = name
    .replace(/^(https?:\/\/)?(www\.)?/, '')
    .replace(/\.(co\.uk|co\.nz|com\.au|co\.ie|org\.uk|net\.au)(\/.*)?$/i, '')
    .replace(/\.(com|co|ie|uk|net|org|io|ai|app|nz|au|ca|us)(\/.*)?$/i, '')
    .replace(/[-_]/g, ' ')

  // Handle camelCase
  cleaned = cleaned.replace(/([a-z])([A-Z])/g, '$1 $2')

  // Common words to split on (business terms, nature, colors, etc.)
  const splitWords = [
    // Business suffixes
    'construction', 'consulting', 'consultants', 'solutions', 'services', 'group', 'agency',
    'studio', 'media', 'digital', 'tech', 'technologies', 'software', 'systems',
    'partners', 'associates', 'industries', 'enterprises', 'holdings', 'corp',
    'corporation', 'company', 'limited', 'ltd', 'inc', 'llc', 'plumbing', 'plumbers',
    'electric', 'electrical', 'mechanical', 'dental', 'medical', 'legal',
    'financial', 'insurance', 'realty', 'properties', 'development', 'design',
    'marketing', 'creative', 'labs', 'works', 'builders', 'contracting',
    'roofing', 'heating', 'cooling', 'hvac', 'landscaping', 'cleaning',
    'painting', 'flooring', 'carpentry', 'masonry', 'welding', 'automotive',
    // Healthcare/veterinary
    'veterinary', 'clinic', 'clinics', 'vets', 'vet', 'animal', 'hospital',
    'pet', 'pets', 'paws', 'smile', 'smiles', 'dentist', 'dentistry', 'surgery',
    'practice', 'wellness', 'health', 'healthcare',
    // Professional services
    'business', 'executive', 'leadership', 'coach', 'coaching', 'life', 'lifestyle',
    'accountant', 'accountants', 'accounting', 'law', 'lawyer', 'lawyers', 'firm',
    'recruitment', 'recruiter', 'recruiters', 'recruiting', 'jobs', 'job', 'hiring',
    'talent', 'staffing', 'experts', 'expert', 'specialist', 'specialists',
    // Common action verbs (for names like "buildandfix", "makeithappen")
    'build', 'fix', 'make', 'work', 'help', 'grow', 'create', 'repair', 'repairs',
    'restore', 'clean', 'move', 'lift', 'run', 'buy', 'sell', 'trade', 'call',
    'book', 'save', 'find', 'get', 'hire', 'rent', 'ship', 'pack', 'haul',
    'happen', 'rise', 'sunrise', 'sunset',
    // Common adjectives (for names like "friendlybuild", "happyhome")
    'friendly', 'happy', 'good', 'great', 'best', 'top', 'new', 'true', 'real',
    'local', 'home', 'safe', 'easy', 'simple', 'perfect', 'total', 'complete',
    'super', 'mega', 'ultra', 'extra', 'premium', 'quality', 'reliable', 'trusted',
    // Conjunctions and prepositions (for names like "buildandfix", "homeforall")
    'and', 'the', 'for', 'all', 'one', 'you', 'your', 'our', 'plus', 'with', 'it',
    // Family terms
    'sons', 'son', 'brothers', 'brother', 'family',
    // Nature words (common in company names) - include coastal before coast
    'coastal', 'oak', 'pine', 'maple', 'cedar', 'willow', 'birch', 'elm', 'ash',
    'river', 'lake', 'hill', 'mount', 'mountain', 'valley', 'creek', 'brook', 'stone',
    'rock', 'wood', 'forest', 'meadow', 'field', 'spring', 'summit', 'peak',
    'bay', 'harbor', 'harbour', 'coast', 'shore', 'bridge', 'gate', 'park',
    'eden', 'grove', 'glen', 'heights', 'view', 'ridge', 'dale', 'haven',
    'island', 'isle', 'beach', 'ocean', 'sea', 'cliff', 'canyon', 'desert', 'prairie',
    // Colors
    'green', 'blue', 'red', 'black', 'white', 'gold', 'golden', 'silver',
    // Directions/positions
    'north', 'south', 'east', 'west', 'central', 'pacific', 'atlantic',
    // Countries/regions (prevents partial matches like "irel and" from "ireland")
    'ireland', 'scotland', 'england', 'wales', 'britain', 'london', 'dublin',
    'australia', 'zealand', 'canada', 'american', 'america', 'texas', 'california',
    'florida', 'european', 'europe', 'asian', 'asia', 'african', 'africa',
    // Common Irish/Scottish surnames (prevents "mcgrathandsons" → "mcgrat hands ons")
    'mcgrath', 'mccarthy', 'mckenna', 'mcdonald', 'mcnamara', 'mcguire', 'mckenzie',
    'macdonald', 'mackenzie', 'macarthur',
    // Major cities (prevents incorrect splits)
    'sydney', 'melbourne', 'brisbane', 'perth', 'auckland', 'wellington',
    'manchester', 'birmingham', 'liverpool', 'leeds', 'bristol', 'brighton',
    'edinburgh', 'glasgow', 'belfast', 'cork', 'galway', 'limerick',
    'toronto', 'vancouver', 'montreal', 'calgary', 'ottawa',
    'chicago', 'boston', 'seattle', 'denver', 'phoenix', 'houston', 'dallas',
    'atlanta', 'miami', 'orlando', 'austin', 'portland', 'harley',
    // Common prefixes/words
    'smart', 'bright', 'clear', 'pure', 'prime', 'first', 'apex', 'alpha',
    'beta', 'omega', 'nova', 'star', 'sun', 'moon', 'sky', 'cloud', 'data',
    'cyber', 'net', 'web', 'app', 'bit', 'byte', 'code', 'logic', 'sync',
    'link', 'hub', 'point', 'base', 'core', 'pro', 'max', 'flex', 'flow',
    'quick', 'fast', 'rapid', 'swift', 'express', 'premier', 'elite', 'royal',
    // Common nouns in business names
    'house', 'hand', 'hands', 'care', 'team', 'crew', 'shop', 'store', 'place',
    'way', 'path', 'road', 'street', 'city', 'town', 'urban', 'metro',
    'finder', 'finders',
  ]

  // Split concatenated words using greedy longest-match algorithm with lookahead
  // This prevents short words like "and" from matching inside longer words like "ireland"
  const sortedWords = [...splitWords].sort((a, b) => b.length - a.length)
  const lowerCleaned = cleaned.toLowerCase()
  const result: string[] = []
  let i = 0

  // Helper: check if string starts with any known word
  const startsWithKnownWord = (str: string): boolean => {
    if (str.length === 0) return true // empty is ok
    const lower = str.toLowerCase()
    return sortedWords.some(w => lower.startsWith(w))
  }

  while (i < cleaned.length) {
    // Skip spaces
    if (cleaned[i] === ' ') {
      result.push(' ')
      i++
      continue
    }

    // Try to match the longest word at current position that doesn't leave orphan fragments
    let matched = false
    for (const word of sortedWords) {
      if (lowerCleaned.substring(i, i + word.length) === word) {
        const remaining = lowerCleaned.substring(i + word.length)
        // Accept match if: remaining is empty, starts with space, or starts with known word
        if (remaining.length === 0 || remaining[0] === ' ' || startsWithKnownWord(remaining)) {
          result.push(' ', cleaned.substring(i, i + word.length), ' ')
          i += word.length
          matched = true
          break
        }
        // Otherwise, try shorter words (continue loop)
      }
    }

    // No valid match - keep the character
    if (!matched) {
      result.push(cleaned[i])
      i++
    }
  }

  cleaned = result.join('')

  // Handle Irish/Scottish names: O'Brien, O'Flaherty, Mc/Mac prefixes
  // But NOT common words starting with 'o' or short suffixes
  const commonOWords = [
    'oak', 'ocean', 'office', 'one', 'open', 'orange', 'order', 'organic',
    'original', 'outdoor', 'owl', 'oxygen', 'on', 'or', 'of', 'our', 'out',
    'over', 'own', 'only', 'other', 'oil', 'old', 'online',
  ]
  cleaned = cleaned
    .split(' ')
    .map(word => {
      const lower = word.toLowerCase()
      // Only apply O' prefix to words starting with 'o' that:
      // - aren't common words
      // - aren't in the splitWords list (like orlando, ottawa)
      // - are at least 4 chars (to avoid false positives like "on", "or")
      if (lower.match(/^o[a-z]/) &&
          !commonOWords.includes(lower) &&
          !splitWords.includes(lower) &&
          lower.length >= 4) {
        return "O'" + word.slice(1)
      }
      return word
    })
    .join(' ')
    .replace(/\bmc([a-z])/gi, 'Mc$1')  // mccarthy -> McCarthy
    .replace(/\bmac([a-z])/gi, 'Mac$1') // macdonald -> MacDonald

  // Clean up multiple spaces and trim
  cleaned = cleaned.replace(/\s+/g, ' ').trim()

  // Capitalize each word properly
  return cleaned
    .split(' ')
    .map(word => {
      // Handle O'Names - keep apostrophe and capitalize after
      if (word.startsWith("O'") || word.startsWith("o'")) {
        return "O'" + word.slice(2).charAt(0).toUpperCase() + word.slice(3).toLowerCase()
      }
      // Handle Mc/Mac names
      if (word.toLowerCase().startsWith('mc') && word.length > 2) {
        return 'Mc' + word.charAt(2).toUpperCase() + word.slice(3).toLowerCase()
      }
      if (word.toLowerCase().startsWith('mac') && word.length > 3) {
        return 'Mac' + word.charAt(3).toUpperCase() + word.slice(4).toLowerCase()
      }
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    })
    .join(' ')
    .trim()
}
