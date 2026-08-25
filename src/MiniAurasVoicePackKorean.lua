local addonName, _ = ...

-- One folder per pack under here, each holding the clip file names MiniAuras ships.
local BASE_PATH = "Interface\\AddOns\\" .. addonName .. "\\Sounds\\"
-- The clips speak Korean spell names, so they are only worth offering on a Korean client.
local LOCALES = { "koKR" }
local PACK_NAMES = { "Hyuk", "Rosa Oh" }

local waiter

---@return boolean handedOver false while MiniAuras has not published its API yet
local function RegisterPacks()
	local api = MiniAurasApi and MiniAurasApi.v1

	if not api or not api.RegisterVoicePack then
		return false
	end

	for i = 1, #PACK_NAMES do
		local name = PACK_NAMES[i]

		api:RegisterVoicePack({
			Name = name,
			Path = BASE_PATH .. name .. "\\",
			Locales = LOCALES,
		})
	end

	return true
end

if not RegisterPacks() then
	-- MiniAuras is an optional dependency, so it normally loads first. It can still arrive
	-- afterwards, and the packs are only offered once it has.
	waiter = CreateFrame("Frame")

	waiter:RegisterEvent("ADDON_LOADED")
	waiter:SetScript("OnEvent", function(self)
		if RegisterPacks() then
			self:UnregisterAllEvents()
		end
	end)
end
