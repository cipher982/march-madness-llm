const path = require('path');

module.exports = function override(config, env) {
    // Exclude the @g-loot/react-tournament-brackets package from source map loader
    config.module.rules.push({
        test: /\.js$/,
        enforce: 'pre',
        use: ['source-map-loader'],
        exclude: [
            path.resolve(__dirname, 'node_modules/@g-loot/react-tournament-brackets'),
        ],
    });

    return config;
};