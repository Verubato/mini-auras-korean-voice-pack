-- The addon is two calls into MiniAuras, so these stub its API and check what it was handed,
-- including the case where MiniAuras is not there yet when the file runs.

local fw = require("TestFramework")
local harness = require("AddonHarness")
local WowMock = require("WowMock")

local ADDON = "MiniAurasVoicePackKorean"
local FILE = "src/MiniAurasVoicePackKorean.lua"

---A stand-in for MiniAuras that records every pack handed to it.
---@param registered table
---@return table
local function NewApi(registered)
	return {
		v1 = {
			RegisterVoicePack = function(_, pack)
				registered[#registered + 1] = pack

				return true
			end,
		},
	}
end

---@param api table? what MiniAuras has published before the addon loads, if anything
---@return table registered
local function LoadWith(api)
	WowMock.Install()

	_G.MiniAurasApi = api

	harness.LoadFiles(ADDON, { FILE }, {})
end

---@return table registered
local function Load()
	local registered = {}

	LoadWith(NewApi(registered))

	return registered
end

fw.describe(ADDON .. " - voice pack registration", function()
	fw.it("hands both packs over when the API is already there", function()
		local registered = Load()

		fw.eq(#registered, 2, "packs registered")
		fw.eq(registered[1].Name, "Hyuk", "first pack name")
		fw.eq(registered[2].Name, "Rosa Oh", "second pack name")
	end)

	fw.it("points each pack at its own folder of clips", function()
		local registered = Load()

		fw.eq(
			registered[1].Path,
			"Interface\\AddOns\\MiniAurasVoicePackKorean\\Sounds\\Hyuk\\",
			"first pack path"
		)
		fw.eq(
			registered[2].Path,
			"Interface\\AddOns\\MiniAurasVoicePackKorean\\Sounds\\Rosa Oh\\",
			"second pack path"
		)
	end)

	fw.it("offers the packs on Korean clients only", function()
		local registered = Load()

		for i = 1, #registered do
			fw.eq(#registered[i].Locales, 1, "locale count for " .. registered[i].Name)
			fw.eq(registered[i].Locales[1], "koKR", "locale for " .. registered[i].Name)
		end
	end)

	fw.it("waits for a MiniAuras that loads after it", function()
		local registered = {}

		LoadWith(nil)

		fw.eq(#registered, 0, "nothing to register against")

		_G.MiniAurasApi = NewApi(registered)
		WowMock.FireEvent("ADDON_LOADED", "MiniAuras")

		fw.eq(#registered, 2, "packs registered once the API arrived")
	end)

	fw.it("hands the packs over once however many addons load after it", function()
		local registered = {}

		LoadWith(nil)

		_G.MiniAurasApi = NewApi(registered)
		WowMock.FireEvent("ADDON_LOADED", "MiniAuras")
		WowMock.FireEvent("ADDON_LOADED", "SomethingElse")

		fw.eq(#registered, 2, "packs registered")
	end)

	fw.it("waits for a MiniAuras too old to know about voice packs", function()
		local registered = {}

		-- The API global exists from 5.0.0, but RegisterVoicePack only from 5.1.0, so its
		-- absence is what says the pack cannot be handed over yet.
		LoadWith({ v1 = {} })

		_G.MiniAurasApi = NewApi(registered)
		WowMock.FireEvent("ADDON_LOADED", "MiniAuras")

		fw.eq(#registered, 2, "packs registered once the real API arrived")
	end)
end)
