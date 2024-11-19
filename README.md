# MiaubotUploader

This project (semi) automates the renaming and organization of media files, generates upload reports, and uploads files to cloud storage using Rclone. 

## Features
---

## Requirements

Before running the project, ensure you have the following prerequisites installed or configured:

- **[Python 3.12 or higher](https://www.python.org/)**: The script is compatible with Python 3.12 and above, which is recommended for optimal performance and compatibility.
- **A valid [TMDb API key](https://www.themoviedb.org/settings/api)**: Required to fetch posters for series and movies.

### Optional Tools
The following tools are optional but enhance the functionality of the project:

- **[FileBot](https://www.filebot.net/)**: Use this tool if you want to automate the renaming and organization of media files into a structured format.
- **[Rclone](https://rclone.org/)**: Use this tool if you want to upload your media files to cloud storage services

---

## File Format Requirements

For the script to work correctly, the input filenames must follow a specific format. Below are examples of input and output formats.

### Input Examples
Ensure filenames include basic information such as title, resolution, platform, and (for series) season/episode data:

```plaintext
attack.on.titan.s01e01.1080p.cr.mkv
Attack.on.Titan.S01E02.1080p.dvd.mkv
YOUR.NAME.2016.1080p.bd.mkv
```

### Output Structure
The script will organize and rename files into the following format:

```plaintext
Attack on Titan (2013)/
├── Season 01/
│   ├── Attack on Titan (2013) - S01E01 - [1080p] [CR] [tmdbid=12345].mkv
│   ├── Attack on Titan (2013) - S01E02 - [1080p] [DVD] [tmdbid=12345].mkv
Your Name (2016) - [1080p] [BD] [tmdbid=12345].mkv
```

---

## FileBot Preset

Use the following preset in FileBot to ensure your files are renamed correctly:

```groovy
{
  // Convert the original filename to uppercase and search for the platform
  def platform = fn.toUpperCase().match(/(?:CR|AMZN|NF|ATVP|MAX|VIX|DSNP|AO|BD|DVD)/) ?: "PLATFORM";

  // Use the TMDb ID if available
  def tmdbId = any{"$tmdbid"}{"$id"};

  // Extract resolution or use a default
  def resolution = vf ?: "1080p";

  if (episode != null) {
    // Series: Organize into seasons and rename
    return "${ny}/Season ${episode.season.pad(2)}/${ny} - S${episode.season.pad(2)}E${episode.episode.pad(2)} - [${resolution}] [${platform}] [tmdbid=${tmdbId}]${'.'+ext}";
  } else if (movie != null) {
    // Movies: Rename into a structured format
    return "${ny} - [${resolution}] [${platform}] [tmdbid=${tmdbId}]${'.'+ext}";
  } else {
    return fn; // Keep original filename if not recognized
  }
}
```

---

## Supported Platforms

The script detects the following platforms automatically based on the filename:

- **Streaming Services**: CR, AMZN, NF, ATVP, MAX, VIX, DSNP, AO
- **Physical Media**: BD (Blu-ray), DVD

If no platform is detected, the script will assign a default value of `PLATFORM`.


---
## Troubleshooting
---

## Contributing

Feel free to submit issues or pull requests to improve this project. Contributions for supporting additional platforms or improving cloud integrations are welcome.

---

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.

---

## Contact

If you have any questions or need assistance, please reach out at 
