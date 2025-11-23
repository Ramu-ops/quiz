# quiz
#  Brain Buster Quiz Game

An interactive, full-featured quiz application with advanced proctoring capabilities, built using Python and Tkinter.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

##  Features

###  Core Functionality
- **Dynamic Question Loading**: Fetches questions from Google Sheets in real-time
- **Random Question Selection**: Each quiz session presents a randomized set of questions
- **Interactive UI**: Beautiful gradient backgrounds with animated elements
- **Skip Option**: Ability to skip difficult questions
- **Instant Feedback**: Visual and textual feedback for correct/incorrect answers
- **Detailed Results**: Comprehensive score breakdown with answer key

###  Anti-Cheating Features
- **Tab Switch Detection**: Automatically terminates quiz if user switches tabs/windows
- **Face Detection**: Monitors user presence via webcam throughout the quiz
- **Eye Tracking Simulation**: Visual indicator showing monitoring is active
- **Movement Detection**: Alerts on excessive body movement
- **Real-time Monitoring**: Live camera feed display with face detection status

###  Visual Elements
- **Animated Emojis**: Colorful, glowing emoji displays
- **Fireworks Animation**: Celebration effects for correct answers
- **Clapping Animation**: Congratulatory animation on quiz completion
- **Dynamic Color Schemes**: Color-coded options and feedback
- **Motivational Quotes**: Random inspirational messages

###  Additional Features
- Real-time date and time display
- Fullscreen mode (toggle with F11 or ESC)
- Tab switch counter
- Face detection status indicator
- Answer key viewer

##  Requirements

### Dependencies
```
tkinter (usually comes with Python)
Pillow (PIL)
opencv-python (cv2)
numpy
requests
```

### System Requirements
- Python 3.8 or higher
- Webcam (for face detection features)
- Internet connection (for loading questions from Google Sheets)

##  Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/brain-buster-quiz.git
   cd brain-buster-quiz
   ```

2. **Install required packages**
   ```bash
   pip install pillow opencv-python numpy requests
   ```

3. **Run the application**
   ```bash
   python quiz_game.py
   ```

##  Setup Instructions

### Google Sheets Configuration

1. Create a Google Sheet with the following columns:
   - `Question`
   - `Option A`
   - `Option B`
   - `Option C`
   - `Option D`
   - `Correct Answer`

2. Make the sheet publicly accessible (Anyone with the link can view)

3. Get your Sheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
   ```

4. Update the `sheet_id` in the code (line 73):
   ```python
   sheet_id = "YOUR_SHEET_ID_HERE"
   ```

### Sample Google Sheet Format

| Question | Option A | Option B | Option C | Option D | Correct Answer |
|----------|----------|----------|----------|----------|----------------|
| How many elements are in periodic table? | 116 | 117 | 118 | 119 | C |
| Which is the most abundant gas? | Nitrogen | Oxygen | CO2 | Hydrogen | A |

##  How to Use

1. **Launch the game** - The quiz starts automatically in fullscreen mode
2. **Read the question** - Question appears with 4 multiple-choice options
3. **Select your answer** - Click on any part of the option to select it
4. **Submit or Skip** - Use the buttons to submit your answer or skip the question
5. **Complete the quiz** - Answer all questions to see your results
6. **View results** - Check your score, view answer key, and play again

##  Controls

- **ESC / F11**: Toggle fullscreen mode
- **Mouse**: Select options by clicking
- **Exit Button**: Close the application

##  Important Notes

### Anti-Cheating System
- The quiz will **terminate immediately** if you:
  - Switch to another window/tab
  - Your face is not detected for an extended period
  - Show excessive movement

### Camera Permissions
- Grant camera access when prompted
- Ensure good lighting for face detection
- Stay centered in the camera view

### Fallback Questions
- If Google Sheets loading fails, the app uses 5 default questions
- Check your internet connection and sheet permissions

##  Customization

### Changing Quiz Duration
Modify the `num_questions` parameter in `select_random_questions()`:
```python
def select_random_questions(self, num_questions=5):  # Change 5 to desired number
```

### Adjusting Colors
Update color codes in the `create_widgets()` and `create_gradient_background()` methods.

### Modifying Monitoring Sensitivity
Adjust threshold values:
```python
# Face detection timeout (line ~177)
if self.looking_away_count > 30:  # Adjust this value

# Movement sensitivity (line ~190)
if dx > 50 or dy > 50 or dw > 30:  # Adjust these thresholds
```

##  Troubleshooting

### Camera Not Working
- Ensure your webcam is connected and not being used by another application
- Check camera permissions in your system settings
- The app will continue without camera monitoring if initialization fails

### Google Sheets Not Loading
- Verify the sheet is publicly accessible
- Check your internet connection
- Confirm the Sheet ID is correct
- The app will use default questions as fallback

### Face Detection Issues
- Ensure adequate lighting
- Remove obstacles between you and the camera
- Adjust your position to be centered in the frame

##  License

This project is licensed under the MIT License - see the LICENSE file for details.

##  Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

##  Contact

For questions or suggestions, please open an issue on GitHub.

##  Acknowledgments

- OpenCV for face detection capabilities
- Tkinter for the GUI framework
- Pillow for image processing
- The Python community for excellent documentation

---

** If you found this project helpful, please consider giving it a ⭐**

Made with ❤️ and Python
