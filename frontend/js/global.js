function openAdminLogin() {
    let currentPosition = 0;
    let resetTimeout;
    let typedSecret = '';
    
    console.log("Admin login listener started!");

    document.addEventListener('keydown', async (event) => {
        if (event.key.length > 1 || event.ctrlKey || event.altKey || event.metaKey) return;

        const pressedKey = event.key.toLowerCase();
        typedSecret += pressedKey;

        try {
            const response = await fetch('/api/verify-keystroke', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    position: currentPosition,
                    key: pressedKey
                })
            });

            const data = await response.json();

            if (data.match) {
                currentPosition = data.next_position;

                if (data.is_complete) {
                    
                    const completeResponse = await fetch('/api/complete-secret', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ secret: typedSecret })
                    });
                    
                    const completeData = await completeResponse.json();
                    
                    if (completeData.success) {
                        window.open(completeData.redirectTo, '_blank');
                    }
                    
                    currentPosition = 0;
                    typedSecret = '';
                }
            } else if (data.reset) {
                currentPosition = 0;
                typedSecret = '';
            }

        } catch (error) {
            currentPosition = 0;
            typedSecret = '';
        }

        clearTimeout(resetTimeout);
        resetTimeout = setTimeout(() => {
            currentPosition = 0;
            typedSecret = '';
        }, 3000);
    });
}

openAdminLogin();