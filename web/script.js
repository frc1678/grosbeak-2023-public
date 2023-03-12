window.Ajv = window.ajv2020

function readAsText(inputElement) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = (e) => {
            resolve(e.target.result)
        }
        reader.onerror = (e) => {
            reject(e)
        }
        reader.readAsText(inputElement.files[0])
    })
}

async function main() {
    const ajv = new Ajv()
    const matchScheduleSchema = await (await fetch("/schemas/match-schedule.json")).json()
    const validateMatchSchedule = ajv.compile(matchScheduleSchema)
    const teamListSchema = await (await fetch("/schemas/team-list.json")).json()
    const validateTeamList = ajv.compile(teamListSchema)

    const apiKeyInput = document.getElementById("apikey")
    const eventKeyInput = document.getElementById("eventkey")

    function getParams() {
        const apiKey = apiKeyInput.value
        const eventKey = eventKeyInput.value
        if (!eventKey) {
            alert("No event key")
            return null
        }
        if (!apiKey) {
            alert("No api key")
            return null
        }
        return {apiKey, eventKey}
    }

    async function uploadFile(type) {
        const params = getParams()
        if (params === null) {
            return
        }
        const {eventKey, apiKey} = params
        let input
        switch (type) {
            case "match-schedule":
                input = matchScheduleFileInput
                break;
            case "team-list":
                input = teamListFileInput
                break;
            default:
                return
        }
        const fileText = await readAsText(input)
        const data = JSON.parse(fileText)
        const response = await fetch("/admin/static", {
            method: "PUT", headers: {
                "Content-Type": "application/json", "Authorization": apiKey
            }, body: JSON.stringify({type, event_key: eventKey, data})
        })
        if (response.ok) {
            alert(`${type} uploaded successfully`)
        } else {
            alert(`Error uploading ${type}: ${await response.text()}`)
        }
    }

    const matchScheduleSubmitButton = document.getElementById("submit-matchschedule")
    const matchScheduleFileInput = document.getElementById("matchschedule")
    matchScheduleFileInput.addEventListener("change", async (v) => {
        const fileText = await readAsText(v.target)
        const valid = validateMatchSchedule(JSON.parse(fileText))
        if (valid) {
            matchScheduleSubmitButton.disabled = false
        } else {
            matchScheduleSubmitButton.disabled = true
            alert("Invalid match schedule")
        }
    })
    matchScheduleSubmitButton.addEventListener("click", async () => {
        uploadFile("match-schedule")
    })
    const teamListSubmitButton = document.getElementById("submit-teamlist")
    const teamListFileInput = document.getElementById("teamlist")
    teamListFileInput.addEventListener("change", async (v) => {
        const fileText = await readAsText(v.target)
        const valid = validateTeamList(JSON.parse(fileText))
        if (valid) {
            teamListSubmitButton.disabled = false
        } else {
            teamListSubmitButton.disabled = true
            alert("Invalid team list")
        }
    })
    teamListSubmitButton.addEventListener("click", async () => {
        uploadFile("team-list")
    })
    const picklistSheetIdInput = document.getElementById("picklist")
    const picklistSheetSubmitButton = document.getElementById("submit-picklist")
    picklistSheetIdInput.addEventListener("input", (ele, ev) => {
        picklistSheetSubmitButton.disabled = ele.data === null
    })
    picklistSheetSubmitButton.addEventListener("click", async () => {
        const sheetId = picklistSheetIdInput.value
        const params = getParams()
        if (params === null) {
            return
        }
        const {eventKey, apiKey} = params
        try {
            fetch("/admin/sheet-id", {method: "POST", headers: {
                "Content-Type": "application/json", "Authorization": apiKey
            }, body: JSON.stringify({event_key: eventKey, sheet_id: sheetId})})
        } catch (error) {
            
        }
    })
}

main()
