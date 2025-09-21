/storage/data/media/movies/
{
    def airdate = d
    def today   = java.time.LocalDate.now()

    // Did it premiere in the last year?
    def cutoff  = today.minusYears(1)

    // Determine if it premiered in the last year based on the above data
    def relDate = d
                 ? d.toInstant().atZone(java.time.ZoneId.systemDefault()).toLocalDate()
                 : java.time.LocalDate.of(y as int, 1, 1)
    relDate.isAfter(cutoff) ? 'New Releases' : 'Movies'
}/
{n} ({y}) [tmdbid-{id}]/
{n} ({y}) [tmdbid-{id}] - [{      
        /* ─── Resolution + source ─── */
        def f     = fn
        def isRip = f =~ /(?i)WEB(?:[-_. ]?RIP|RIP)/
        def isDl  = f =~ /(?i)WEB(?:[-_. ]?DL|DL)/
        def src   = null

        // Streaming
        if      (f =~ /(?i)(AMZN|Amazon)/)                         { src = 'AMZN '    + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /(NF|Netflix)/)                              { src = 'NF '      + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /(?i)(DSNP|Disney\+?|D\+)/)                  { src = 'DSNP '    + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /(HMAX|MAX|HBO[-_. ]?Max)/)                  { src = 'HMAX '    + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /(?i)HULU/)                                  { src = 'HULU '    + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /(?i)(ATV(P|\+)?|Apple.*TV)/)                { src = 'ATVP '    + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /(?i)(PMNT|Paramount|PMTP)/)                 { src = 'PMTP '    + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /(?i)(PCOK|PCK|PEACOCK)/)                    { src = 'PCOK '    + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /(CR|Crunchyroll)/)                          { src = 'CR '      + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /(AO|Anime.*Onegai)/)                        { src = 'AO '      + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /(?i)VIKI/)                                  { src = 'VIKI '    + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /(?i)VIX/)                                   { src = 'VIX '     + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /(?i)CLARO/)                                 { src = 'CLARO '   + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /MA/)                                        { src = 'MA '      + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /iT|iTunes/)                                 { src = 'iT '      + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /CTHP/)                                      { src = 'CTHP '    + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /(?i)UNSP/)                                  { src = 'UNSP '    + (isRip ? 'WEBRip' : 'WEB-DL') }
        else if (f =~ /(?i)FLOW/)                                  { src = 'FLOW '    + (isRip ? 'WEBRip' : 'WEB-DL') }

        // Generic WEB
        else if (isRip)                                            { src = 'WEBRip' }
        else if (isDl)                                             { src = 'WEB-DL' }
        // HDTV
        else if (f =~ /(?i)HDTV/)                                  { src = 'HDTV' }
        else if (f =~ /(?i)HDrip/)                                 { src = 'HDrip' }

        // Blu-ray / Remux
        else if (f =~ /(?i)BDRemux/)                               { src = 'BDRemux' }
        else if (f =~ /(?i)(BluRay|BRRip|BDRip|BDMux|BD)/)         { src = 'BD' }

        vf + (src ? ' ' + src : '')
    }]
{ hdr ? ' [' + (hdr =~ /(?i)Dolby Vision/ ? 'DV' : hdr) + '] ' : ' ' }
 [{
    bitDepth ? bitDepth + 'bit' : ''
}] [{mbps}]
 [{
    // Normalize video codecs
    def videoCodec = vc
    if (videoCodec =~ /(?i)x264/) {
        videoCodec = 'AVC'
    } else if (videoCodec =~ /(?i)x265/) {
        videoCodec = 'HEVC'
    }
    videoCodec
}] [{ac} {channels}]
 [{
    def langs = audio*.Language.findAll{ it }.unique()
    langs ? langs.join(', ') : 'und'
}]
 [{
    def subs  = text*.Language.findAll{ it }.unique()
    subs ? subs.join(', ') : 'und'
}]
{
    // Extract release group from filename, maintaining original case
    def g = null
    def originalFileName = fn
    
    // Pattern 1: Group at the beginning in brackets [GroupName]
    def pattern1 = originalFileName =~ /^\[([^\]]+)\]/
    if (pattern1) {
        def candidate = pattern1[0][1].trim()
        // Validate that it's a real group name (no resolution, codecs, or quality indicators)
        if (!candidate.matches(/(?i).*(?:\d+p|x264|x265|h\.?264|h\.?265|hevc|avc|webdl|webrip|brrip|bluray|dvdrip|hdtv|web|bd|remux|\d+(?:\.\d+)?\s*(?:gb|mb)|atmos|dts|ac3|aac|flac|mp3|\d+(?:\.\d+)?\s*mbps?).*/)) {
            g = candidate
        }
    }
    // Pattern 2: Group at the end after dash - but handle groups with internal dashes
    else {
        // Look for pattern like "- GroupName" or "- Group-Name" at the end
        def pattern2 = originalFileName =~ /.*\s-\s([A-Za-z0-9][A-Za-z0-9\-_]*[A-Za-z0-9])(?:\.[^.]+)?$/
        if (pattern2) {
            def candidate = pattern2[0][1].trim()
            // Much stricter validation - must not contain technical terms or be too short
            if (candidate && 
                candidate.length() >= 3 && 
                candidate.length() <= 25 &&
                !candidate.matches(/(?i).*(?:\d+p|x264|x265|h\.?264|h\.?265|hevc|avc|webdl|webrip|brrip|bluray|dvdrip|hdtv|web|bd|remux|\d+(?:\.\d+)?\s*(?:gb|mb)|atmos|dts|ac3|aac|flac|mp3|\d+(?:\.\d+)?\s*mbps?|mkv|mp4|avi|mov|\d{4}|\([^)]*\)).*/) &&
                !candidate.matches(/(?i)^(?:english|spanish|french|german|italian|portuguese|japanese|korean|chinese|hindi|russian|arabic|dutch|swedish|norwegian|danish|finnish)$/) &&
                !candidate.matches(/(?i)^\d+$/) &&
                candidate.matches(/^[A-Za-z0-9\-_]+$/)) {
                g = candidate
            }
        }
        // Pattern 3: Group after dash without space (e.g., H.264-GroupName)
        else {
            def pattern3 = originalFileName =~ /.*-([A-Za-z0-9][A-ZaZ0-9\-_]*[A-Za-z0-9])(?:\.[^.]+)?$/
            if (pattern3) {
                def candidate = pattern3[0][1].trim()
                if (candidate && 
                    candidate.length() >= 3 && 
                    candidate.length() <= 25 &&
                    !candidate.matches(/(?i).*(?:\d+p|x264|x265|h\.?264|h\.?265|hevc|avc|webdl|webrip|brrip|bluray|dvdrip|hdtv|web|bd|remux|\d+(?:\.\d+)?\s*(?:gb|mb)|atmos|dts|ac3|aac|flac|mp3|\d+(?:\.\d+)?\s*mbps?|mkv|mp4|avi|mov|\d{4}|\([^)]*\)).*/) &&
                    !candidate.matches(/(?i)^(?:english|spanish|french|german|italian|portuguese|japanese|korean|chinese|hindi|russian|arabic|dutch|swedish|norwegian|danish|finnish)$/) &&
                    !candidate.matches(/(?i)^\d+$/) &&
                    candidate.matches(/^[A-Za-z0-9\-_]+$/)) {
                    g = candidate
                }
            }
        }
    }
    
    // Strip trailing _muxed (case-insensitive) if present
    g = g?.replaceAll(/(?i)_muxed$/, '')

    // Return formatted suffix or nothing
    g ? ' - ' + g : ''
}
