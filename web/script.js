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
        return {apikey: apiKeyInput.value, eventkey: eventKeyInput.value}
    }
    async function uploadFile(type) {
        const {eventkey, apikey} = getParams()
            if (!eventkey) {
                alert("No event key")
                return
            }
            if (!apikey) {
                alert("No api key")
                return
            }
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
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": apikey
                },
                body: JSON.stringify({type, event_key: eventkey, data})
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
    matchScheduleSubmitButton.addEventListener("click", async () => {
        uploadFile("match-schedule")
    })
    teamListSubmitButton.addEventListener("click", async () => {
        uploadFile("team-list")
    })

}


main()