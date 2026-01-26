import ui
import player
import app

# AFFECT_ENERGY_CRYSTAL type (must match server's AFFECT_ENERGY_CRYSTAL in affect.h)
AFFECT_ENERGY_CRYSTAL = 536

class EnergyGauge(ui.Window):
	GAUGE_PATH = "d:/ymir work/ui/pattern/energygauge/"
	GAUGE_WIDTH = 95
	GAUGE_HEIGHT = 13

	def __init__(self):
		ui.Window.__init__(self)

		self.isActive = False
		self.endTime = 0
		self.totalDuration = 0

		self.__CreateUI()
		self.Hide()

	def __del__(self):
		ui.Window.__del__(self)

	def __CreateUI(self):
		self.SetSize(self.GAUGE_WIDTH + 10, self.GAUGE_HEIGHT + 30)
		self.SetPosition(10, 200)  # Left side of screen

		# Background (empty gauge)
		self.imgBackground = ui.ExpandedImageBox()
		self.imgBackground.SetParent(self)
		self.imgBackground.SetPosition(0, 15)
		self.imgBackground.LoadImage(self.GAUGE_PATH + "gauge_empty.tga")
		self.imgBackground.Show()

		# Gauge fill
		self.imgGauge = ui.ExpandedImageBox()
		self.imgGauge.SetParent(self)
		self.imgGauge.SetPosition(0, 15)
		self.imgGauge.LoadImage(self.GAUGE_PATH + "gauge_full.tga")
		self.imgGauge.Show()

		# Title text
		self.textTitle = ui.TextLine()
		self.textTitle.SetParent(self)
		self.textTitle.SetPosition(0, 0)
		self.textTitle.SetText("Energie")
		self.textTitle.SetFontColor(1.0, 0.8, 0.2)
		self.textTitle.Show()

		# Time remaining text
		self.textTime = ui.TextLine()
		self.textTime.SetParent(self)
		self.textTime.SetPosition(0, self.GAUGE_HEIGHT + 18)
		self.textTime.SetText("")
		self.textTime.SetFontColor(1.0, 1.0, 1.0)
		self.textTime.Show()

	def Destroy(self):
		self.imgBackground = None
		self.imgGauge = None
		self.textTitle = None
		self.textTime = None

	def SetEnergyAffect(self, duration):
		"""Called when energy crystal affect is added"""
		self.isActive = True
		self.totalDuration = duration
		self.endTime = app.GetTime() + duration
		self.Show()
		self.__RefreshGauge()

	def RemoveEnergyAffect(self):
		"""Called when energy crystal affect is removed"""
		self.isActive = False
		self.endTime = 0
		self.totalDuration = 0
		self.Hide()

	def __RefreshGauge(self):
		if not self.isActive:
			return

		currentTime = app.GetTime()
		remainingTime = max(0, self.endTime - currentTime)

		if remainingTime <= 0:
			self.RemoveEnergyAffect()
			return

		# Calculate percentage
		if self.totalDuration > 0:
			percentage = float(remainingTime) / float(self.totalDuration)
		else:
			percentage = 0.0

		percentage = max(0.0, min(1.0, percentage))

		# Update gauge width
		gaugeWidth = int(self.GAUGE_WIDTH * percentage)
		self.imgGauge.SetScale(percentage, 1.0)

		# Update time text
		minutes = int(remainingTime / 60)
		seconds = int(remainingTime % 60)
		self.textTime.SetText("%d:%02d" % (minutes, seconds))

		# Change gauge color based on remaining time
		if percentage > 0.5:
			self.imgGauge.LoadImage(self.GAUGE_PATH + "gauge_full.tga")
		elif percentage > 0.2:
			self.imgGauge.LoadImage(self.GAUGE_PATH + "gauge_hungry.tga")
		else:
			self.imgGauge.LoadImage(self.GAUGE_PATH + "gauge_empty.tga")

	def OnUpdate(self):
		if self.isActive:
			self.__RefreshGauge()
