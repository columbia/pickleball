import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.family"] = "serif"
plt.rcParams["mathtext.fontset"] = "dejavuserif"


categories = [
    "GGUF",
    "SafeTensors Only",
    "Pickle",  # Will show stacked components
]

# Model percentages
pickle_model_values = [17.3, 33.9, [26.6, 18.3]]  # [GGUF, SafeTensors Only, [Pickle Only, Pickle+ST]]
pickle_download_values = [5.0, 12.7, [19.1, 61.4]]  # [GGUF, SafeTensors Only, [Pickle Only, Pickle+ST]]

# Assigning colors
colors = ["#1f77b4", "#24b24b", ["#d62728", "#ff7f0e"]]  # Reversed order

# Create a horizontal bar plot
fig, ax = plt.subplots(figsize=(10, 3))

# Function to create bars with stacked components for Pickle
def create_bars(positions, values, height, label, hatch=None):
    bars = []
    for i, (val, color) in enumerate(zip(values, colors)):
        if isinstance(val, list):  # For Pickle category
            x_pos = 0
            for v, c in zip(val, color):
                bar = ax.barh(positions[i], v, left=x_pos, 
                            color=c, height=height, label=None)
                if hatch:
                    # Set hatch for each rectangle in the bar
                    bar[0].set_hatch(hatch)
                x_pos += v
                bars.append(bar)
        else:  # For other categories
            bar = ax.barh(positions[i], val, color=color, height=height, label=None)
            if hatch:
                # Set hatch for each rectangle in the bar
                bar[0].set_hatch(hatch)
            bars.append(bar)
    return bars

# Create bars
positions = np.arange(len(categories))
bars1 = create_bars(positions + 0.2, pickle_model_values, 0.3, 'Proportion of Models')
bars2 = create_bars(positions - 0.2, pickle_download_values, 0.3, 'Proportion of Downloads', '///')

# Add text labels to the bars
def add_labels(values, y_offset):
    for i, val in enumerate(values):
        if isinstance(val, list):  # For Pickle category
            x_pos = 0
            total = sum(val)
            # Add individual percentages in the middle of each segment
            for v in val:
                # Add white background to text for better visibility
                ax.text(x_pos + v/2, i + y_offset, f"{v}%", 
                       va='center', ha='center', fontsize=16,
                       bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=1))
                x_pos += v
            # Add total percentage at the end
            ax.text(total + 1, i + y_offset, f"{total:.1f}%", 
                   va='center', fontsize=16,
                   bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=1))
        else:
            ax.text(val + 1, i + y_offset, f"{val}%", 
                   va='center', fontsize=16,
                   bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=1))

add_labels(pickle_model_values, 0.2)
add_labels(pickle_download_values, -0.2)

# Labels and formatting
ax.set_xlabel("Percentage (%)", fontsize=20)
# ax.set_title("Model Format Distribution Collected in March 2025", fontsize=20, pad=30, fontweight='bold')
ax.set_xlim(0, 100)  # Adjusted to show full percentage range
ax.set_yticks(positions)
ax.tick_params(axis='both', labelsize=15, width=2)
ax.set_yticklabels(categories, fontsize=18, fontweight='bold')

ax.spines['top'].set_visible(True)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(True)
ax.xaxis.set_ticks_position('bottom')
ax.yaxis.set_ticks_position('none')

# Create custom legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='gray', label='Proportion of Models'),
    Patch(facecolor='gray', hatch='///', label='Proportion of Downloads'),
    Patch(facecolor='#ff7f0e', label='Pickle + ST'),
    Patch(facecolor='#d62728', label='Pickle Only')
]
ax.legend(handles=legend_elements, bbox_to_anchor=(1.0, 0), 
         loc='lower right', fontsize=17)

# Remove gridlines
ax.grid(False)

# Save the figure
plt.savefig("figure3.pdf", 
            bbox_inches='tight', format='pdf')

# Show the plot
plt.show()