var calculate;
(function (calculate) {
    function calculateSellerPrice(amount, publisherFee) {
        if (publisherFee === void 0) { publisherFee = 0.1; }
        function getFees(receivedAmount, publisherFee) {
            var _a = {
                wallet_fee_base: 0,
                wallet_fee_percent: 0.05,
                wallet_fee_minimum: 1
            }, wallet_fee_base = _a.wallet_fee_base, wallet_fee_percent = _a.wallet_fee_percent, wallet_fee_minimum = _a.wallet_fee_minimum;
            var nSteamFee = Math.floor(Math.max(receivedAmount * wallet_fee_percent, wallet_fee_minimum) + wallet_fee_base);
            var nPublisherFee = Math.floor(publisherFee > 0 ? Math.max(receivedAmount * publisherFee, 1) : 0);
            var nAmountToSend = receivedAmount + nSteamFee + nPublisherFee;
            return {
                steam_fee: nSteamFee,
                publisher_fee: nPublisherFee,
                fees: nSteamFee + nPublisherFee,
                amount: ~~nAmountToSend
            };
        }
        var _a = {
            wallet_fee_base: 0,
            wallet_fee_percent: 0.05
        }, wallet_fee_base = _a.wallet_fee_base, wallet_fee_percent = _a.wallet_fee_percent;
        var iterations = 0;
        var estimatedReceivedValue = (amount - wallet_fee_base) / (wallet_fee_percent + publisherFee + 1);
        var undershot = false;
        var fees = getFees(estimatedReceivedValue, publisherFee);
        while (fees.amount != amount && iterations < 10) {
            if (fees.amount > amount) {
                if (undershot) {
                    fees = getFees(estimatedReceivedValue - 1, publisherFee);
                    fees.steam_fee += (amount - fees.amount);
                    fees.fees += (amount - fees.amount);
                    fees.amount = amount;
                    break;
                }
                else {
                    estimatedReceivedValue--;
                }
            }
            else {
                undershot = true;
                estimatedReceivedValue++;
            }
            fees = getFees(estimatedReceivedValue, publisherFee);
            iterations++;
        }
        return fees;
    }
    function update(caller, buyer_pays) {
        var val = 0;
        if (caller == 'buyer') {
            val = +buyer_pays;
            if (isNaN(val) || !isFinite(val))
                return;
            if (val < 0.03)
                val = 0.03;
            var calc = calculateSellerPrice(~~(val * 100));
            you_receive = "".concat((calc.amount - calc.fees) / 100);
            steam_fees = "".concat(calc.fees / 100);
            return steam_fees + ',' + you_receive
        }
    }
    calculate.update = update;
})(calculate || (calculate = {}));

module.exports = calculate.update;