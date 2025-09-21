/storage/data/media/shows/{
    // Determine series type based on genres and origin
    
    // Anime (Animation/Anime + Japanese/Chinese/Korean)
    if (genres =~ /(?i)(Animation|Anime)/ && (country =~ /(?i)(JPN|CHN|KOR)/ || language =~ /(?i)(jpn|chn|kor)/)) {
        def seasonYear = d ? d.year : y
        if (seasonYear >= 2020) {
            'Anime Ongoing'
        } else {
            'Anime'
        }
    }
    // Other animated series
    else if (genres =~ /(?i)(Animation|Anime)/) {
        'Animation'
    }
    // Asian drama (not anime)
    else if (country =~ /(?i)(JPN|KOR|CHN|THA|TWN|HKG|SGP)/ && !(genres =~ /(?i)(Animation|Anime)/)) {
        'Asian Drama'
    }
    else {
        'TV Shows'
    }
}/{
    // Seasonal structure for recent anime
    if (genres =~ /(?i)(Animation|Anime)/ && (country =~ /(?i)(JPN|CHN|KOR)/ || language =~ /(?i)(jpn|chn|kor)/)) {
        def seasonYear = d ? d.year : y
        def currentYear = java.time.LocalDate.now().year
        
        if (seasonYear >= 2020) {
            // Current year uses seasonal structure
            if (seasonYear == currentYear) {
                def seasonMonth = d ? d.month : 1
                def season = switch (seasonMonth) {
                    case 1..3 -> 'winter'
                    case 4..6 -> 'spring'
                    case 7..9 -> 'summer'
                    case 10..12 -> 'fall'
                    default -> 'winter'
                }
                seasonYear + '/' + season + '/'
            }
            // Recent but not current year, just use year
            else {
                seasonYear + '/'
            }
        } else {
            ''
        }
    } else {
        ''
    }
}/{ny} [tvdbid-{tvdbid}]/Season { (episode.special != null ? '00' : episode.season.pad(2)) }/
{ny} - S{ (episode.special != null ? '00' : episode.season.pad(2)) }E{
    // Multi-episode files
    if (episode.special != null) {
        episode.special.pad(2)
    } else {
        def eps = episodes.collect{ it.episode }.sort()
        if (eps.size() > 1) {
            eps.first().pad(2) + '-E' + eps.last().pad(2)
        } else {
            episode.episode.pad(2)
        }
    }
}
      { 
        // Multi-episode absolute numbers
        if (absolute) {
            def absEps = episodes.collect{ it.absolute }.findAll{ it != null }.sort()
            if (absEps.size() > 1) {
                ' - ' + absEps.first().pad(3) + '-' + absEps.last().pad(3)
            } else {
                ' - ' + absolute.pad(3)
            }
        } else {
            ''
        }
      } - [{
    /* Resolution + source */
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
    else if (f =~ /FLOW/)                                      { src = 'FLOW '    + (isRip ? 'WEBRip' : 'WEB-DL') }

    // Generic WEB
    else if (isRip)                                            { src = 'WEBRip' }
    else if (isDl)                                             { src = 'WEB-DL' }

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
    // Release group extraction
    def g = null
    def originalFileName = fn
    
    // Pattern 1: Group in brackets [GroupName]
    def pattern1 = originalFileName =~ /^\[([^\]]+)\]/
    if (pattern1) {
        def candidate = pattern1[0][1].trim()
        if (!candidate.matches(/(?i).*(?:\d+p|x264|x265|h\.?264|h\.?265|hevc|avc|webdl|webrip|brrip|bluray|dvdrip|hdtv|web|bd|remux|\d+(?:\.\d+)?\s*(?:gb|mb)|atmos|dts|ac3|aac|flac|mp3|\d+(?:\.\d+)?\s*mbps?).*/)) {
            g = candidate
        }
    }
    // Pattern 2: Group after dash
    else {
        def pattern2 = originalFileName =~ /.*\s-\s([A-Za-z0-9][A-Za-z0-9\-_]*[A-Za-z0-9])(?:\.[^.]+)?$/
        if (pattern2) {
            def candidate = pattern2[0][1].trim()
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
            def pattern3 = originalFileName =~ /.*-([A-Za-z0-9][A-Za-z0-9\-_]*[A-Za-z0-9])(?:\.[^.]+)?$/
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
    
    g = g?.replaceAll(/(?i)_muxed$/, '')
    g ? ' - ' + g : ''
}
