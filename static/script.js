const jdInput = document.getElementById("jdInput");

const charCount = document.getElementById("charCount");

const generateBtn =
    document.getElementById("generateBtn");

const btnText =
    document.getElementById("btnText");

const loader =
    document.getElementById("loader");

const progressCard =
    document.getElementById("progressCard");

const resultCard =
    document.getElementById("resultCard");

const errorBox =
    document.getElementById("errorBox");

const errorText =
    document.getElementById("errorText");

const progressBar =
    document.getElementById("progressBar");

const progressText =
    document.getElementById("progressText");

const downloadBtn =
    document.getElementById("downloadBtn");



/* --------------------------------
   Character Counter
-------------------------------- */

jdInput.addEventListener(
    "input",
    () => {

        const count =
            jdInput.value.length;

        charCount.textContent =
            `${count.toLocaleString()} characters`;

    }
);



/* --------------------------------
   Generate Resume
-------------------------------- */

generateBtn.addEventListener(
    "click",
    async () => {

        const jd =
            jdInput.value.trim();


        if (!jd) {

            showError(
                "Please paste the Job Description first."
            );

            return;

        }


        hideError();

        resultCard.classList.add("hidden");

        progressCard.classList.remove("hidden");


        setLoading(true);


        try {

            /* Step 1 */

            updateProgress(
                15,
                "Analyzing job description..."
            );


            await sleep(500);


            /* Step 2 */

            updateProgress(
                35,
                "Analyzing GitHub repositories..."
            );


            await sleep(500);


            /* API */

            const response =
                await fetch(
                    "/generate-resume",
                    {

                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            jd_text: jd
                        })

                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Resume generation failed."
                );

            }


            /* Step 3 */

            updateProgress(
                75,
                "Generating tailored resume..."
            );


            await sleep(500);


            /* Step 4 */

            updateProgress(
                100,
                "PDF generated successfully."
            );


            await sleep(500);


            progressCard.classList.add(
                "hidden"
            );


            resultCard.classList.remove(
                "hidden"
            );


            downloadBtn.href =
                data.download_url;


        }
        catch (error) {

            progressCard.classList.add(
                "hidden"
            );

            showError(
                error.message
            );

        }
        finally {

            setLoading(false);

        }

    }
);



/* --------------------------------
   Loading
-------------------------------- */

function setLoading(isLoading) {

    generateBtn.disabled =
        isLoading;


    if (isLoading) {

        btnText.textContent =
            "Generating Resume...";

        loader.classList.remove(
            "hidden"
        );

    }
    else {

        btnText.textContent =
            "🚀 Generate Tailored Resume";

        loader.classList.add(
            "hidden"
        );

    }

}



/* --------------------------------
   Progress
-------------------------------- */

function updateProgress(
    percentage,
    message
) {

    progressBar.style.width =
        `${percentage}%`;

    progressText.textContent =
        message;

}



/* --------------------------------
   Error
-------------------------------- */

function showError(message) {

    errorBox.classList.remove(
        "hidden"
    );

    errorText.textContent =
        message;

}


function hideError() {

    errorBox.classList.add(
        "hidden"
    );

}



/* --------------------------------
   Utility
-------------------------------- */

function sleep(ms) {

    return new Promise(
        resolve => setTimeout(
            resolve,
            ms
        )
    );

}