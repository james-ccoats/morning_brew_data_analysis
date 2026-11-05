# Run from the project root (open MorningBrewViz.Rproj, or `Rscript scripts/05_plot_weekly_change.R`)
library(tidyverse)
library(ggthemes)
library(scales)

df <- read_csv("data/cleaned/weekly_comparison.csv")

mbi_plot <- ggplot(data = df, mapping = aes(x = date))+
  geom_line(mapping = aes(y = portfolio_value), color = "#4a8fff", show.legend = TRUE)+
  geom_line(mapping = aes(y = spy_value), color = "grey")+
  annotate("label", label = "MBI", x = ymd("2026-08-01"), y = 1200, color = "#4a8fff")+
  annotate("label", label = "SPY", x = ymd("2026-08-01"), y = 1000, color = "grey")+
  theme_minimal()+
  scale_y_continuous(labels = label_dollar(), breaks = seq(0, 1200, 200))+
  labs(title = "Growth of the \"Morning Brew Index\" (MBI)",
       subtitle = "Since August 2025, investing $25 each week into the Morning Brew Daily Show's stock of the week \nhas returned 18.5% on total dollars invested, vs. 13.2% for the same strategy applied to SPY.",
       x = "Date",
       y = "Value ($)")+
  theme(plot.title = element_text(size = 20))

ggsave("assets/mbi.png", plot = mbi_plot, width = 8.3, height = 5.4, dpi = 100, bg = "white")
