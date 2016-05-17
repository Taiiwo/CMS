'use strict';

/*
 * main.js
 *
 * New Age Bullshit Generator
 * © 2014-15 Seb Pearce (sebpearce.com)
 * Licensed under the MIT License.
 *
 */

// Toolkit of useful functions
var kit = {

  copyArrayOfArrays: function copyArrayOfArrays(arr) {
    var result = [];
    for (var i = 0; i < arr.length; i++) {
      result[i] = arr[i].slice();
    }
    return result;
  },

  capitalizeFirstLetter: function capitalizeFirstLetter(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  },

  randomInt: function randomInt(max) {
    return Math.floor(Math.random() * (max + 1));
  }

};

// The generator in all its quantum glory
function BS(){

  this.sentencePool = [];

  this.initializeSentencePool = function() {
    this.sentencePool = [];
    this.sentencePool = kit.copyArrayOfArrays(this.sentencePatterns);
  }

  this.removeSentenceFromPool = function(topic, el) {
    if (el > -1) {
      this.sentencePool[topic].splice(el, 1);
    }
  }

  this.retrieveRandomWordOfType = function(type) {
    var rand = kit.randomInt(this.bullshitWords[type].length - 1);
    return this.bullshitWords[type][rand];
  }

  this.generateSentence = function(topic) {

    var patternNumber = kit.randomInt(this.sentencePool[topic].length - 1);
    var pattern = this.sentencePool[topic][patternNumber];

    // insert a space before . , ; ? so we can split the string into an array
    var pattern = pattern.replace(/([\.,;\?])/g, ' $1');
    var pattern = pattern.split(' ');

    // remove the pattern from the sentence pool so it can't be re-used
    this.removeSentenceFromPool(topic, patternNumber);

    // remove the topic from the sentence pool if there are no sentences left
    // for that particular topic
    if (this.sentencePool[topic].length === 0) {
      this.sentencePool.splice(topic, 1);
    }

    var result = '';
    for (var x in pattern) {
      // if word matches one of the placeholder words (e.g. nPerson),
      // replace it with a random instance of its type (e.g. warrior)
      if (this.bullshitWords.hasOwnProperty(pattern[x])) {
        result += this.retrieveRandomWordOfType(pattern[x]);
      } else {
        result += pattern[x];
      }
      result += ' ';
    }

    // replace 'a [vowel]' with 'an [vowel]'
    // I added a \W before the [Aa] because one time I got
    // 'Dogman is the antithesis of knowledge' :)
    result = result.replace(/(^|\W)([Aa]) ([aeiou])/g, '$1$2n $3');

    result = result.trim();
    result = kit.capitalizeFirstLetter(result);

    // remove spaces before commas/periods/semicolons
    result = result.replace(/ ([,\.;\?])/g, '$1');
    // take care of prefixes (delete the space after the hyphen)
    result = result.replace(/- /g, '-');
    // add space after question marks if they're mid-sentence
    result = result.replace(/\?(\w)/g, '? $1');

    return result;
  }

  this.generateText = function(numberOfSentences, sentenceTopic) {

    var fullText = '';
    for (var i = 0; i < numberOfSentences; i++) {
      // if the topic has been deleted, pick another topic
      if (typeof this.sentencePool[sentenceTopic] == 'undefined') {
        sentenceTopic = kit.randomInt(this.sentencePool.length - 1);
      }
      fullText += this.generateSentence(sentenceTopic);
    }

    // insert a space between sentences (after periods and question marks)
    fullText = fullText.replace(/([\.\?])(\w)/g, '$1 $2');

    return fullText;
  }

  this.sentencePatterns = [
    [   // explaining
      'nMass is the driver of nMass.',
      'nMass is the nTheXOf of nMass, and of us.',
      'You and I are nPersonPlural of the nCosmos.',
      'We exist as fixedNP.',
      'We viPerson, we viPerson, we are reborn.',
      'Nothing is impossible.',
      'This life is nothing short of a ing nOf of adj nMass.',
      'Consciousness consists of fixedNP of quantum energy. “Quantum” means a ing of the adj.',
      'The goal of fixedNP is to plant the seeds of nMass rather than nMassBad.',
      'nMass is a constant.',
      'By ing, we viPerson.',
      'The nCosmos is adjWith fixedNP.',
      'To vTraverse the nPath is to become one with it.',
      'Today, science tells us that the essence of nature is nMass.',
      'nMass requires exploration.',
    ],
    [   // warnings
      'We can no longer afford to live with nMassBad.',
      'Without nMass, one cannot viPerson.',
      'Only a nPerson of the nCosmos may vtMass this nOf of nMass.',
      'You must take a stand against nMassBad.',
      'Yes, it is possible to vtDestroy the things that can vtDestroy us, but not without nMass on our side.',
      'nMassBad is the antithesis of nMass.',
      'You may be ruled by nMassBad without realizing it. Do not let it vtDestroy the nTheXOf of your nPath.',
      'The complexity of the present time seems to demand a ing of our nOurPlural if we are going to survive.',
      'nMassBad is born in the gap where nMass has been excluded.',
      'Where there is nMassBad, nMass cannot thrive.',
    ],
    [   // future hope
      'Soon there will be a ing of nMass the likes of which the nCosmos has never seen.',
      'It is time to take nMass to the next level.',
      'Imagine a ing of what could be.',
      'Eons from now, we nPersonPlural will viPerson like never before as we are ppPerson by the nCosmos.',
      'It is a sign of things to come.',
      'The future will be a adj ing of nMass.',
      'This nPath never ends.',
      'We must learn how to lead adj lives in the face of nMassBad.',
      'We must vtPerson ourselves and vtPerson others.',
      'The nOf of nMass is now happening worldwide.',
      'We are being called to explore the nCosmos itself as an interface between nMass and nMass.',
      'It is in ing that we are ppPerson.',
      'The nCosmos is approaching a tipping point.',
    ],
    [   // you and your problems
      'Although you may not realize it, you are adj.',
      'nPerson, look within and vtPerson yourself.',
      'Have you found your nPath?',
      'How should you navigate this adj nCosmos?',
      'It can be difficult to know where to begin.',
      'If you have never experienced this nOf fixedAdvP, it can be difficult to viPerson.',
      'The nCosmos is calling to you via fixedNP. Can you hear it?',
    ],
    [   // history
      'Throughout history, humans have been interacting with the nCosmos via fixedNP.',
      'Reality has always been adjWith nPersonPlural whose nOurPlural are ppThingPrep nMass.',
      'Our conversations with other nPersonPlural have led to a ing of adjPrefix adj consciousness.',
      'Humankind has nothing to lose.',
      'We are in the midst of a adj ing of nMass that will vOpenUp the nCosmos itself.',
      'Who are we? Where on the great nPath will we be ppPerson?',
      'We are at a crossroads of nMass and nMassBad.',
    ],
    [   // selling point
      'Through nSubject, our nOurPlural are ppThingPrep nMass.',
      'nSubject may be the solution to what’s holding you back from a adjBig nOf of nMass.',
      'You will soon be ppPerson by a power deep within yourself — a power that is adj, adj.',
      'As you viPerson, you will enter into infinite nMass that transcends understanding.',
    ]

  ];

  this.bullshitWords = {
    nCosmos: [
  		'cosmos',
  		'quantum soup',
  		'infinite',
  		'universe',
  		'galaxy',
  		'multiverse',
  		'grid',
  		'quantum matrix',
  		'totality',
  		'quantum cycle',
  		'nexus',
  		'planet',
  		'solar system',
  		'world',
  		'stratosphere',
  		'dreamscape',
  		'biosphere',
  	],
    nPerson: [
  		'being',
  		'child',
  		'traveller',
  		'entity',
  		'lifeform',
  		'wanderer',
  		'visitor',
  		'prophet',
  		'seeker',
  	],
    nPersonPlural: [
  		'beings',
  		'travellers',
  		'entities',
  		'lifeforms',
  		'dreamweavers',
  		'adventurers',
  		'pilgrims',
  		'warriors',
  		'messengers',
  		'dreamers',
  		'storytellers',
  		'seekers',
  	],
    nMass: [
  		'consciousness',
  		'nature',
  		'beauty',
  		'knowledge',
  		'truth',
  		'life',
  		'healing',
  		'potential',
  		'freedom',
  		'purpose',
  		'coherence',
  		'choice',
  		'passion',
  		'understanding',
  		'balance',
  		'growth',
  		'inspiration',
  		'conscious living',
  		'energy',
  		'health',
  		'spacetime',
  		'learning',
  		'being',
  		'wisdom',
  		'stardust',
  		'sharing',
  		'science',
  		'curiosity',
  		'hope',
  		'wonder',
  		'faith',
  		'fulfillment',
  		'peace',
  		'rebirth',
  		'self-actualization',
  		'presence',
  		'power',
  		'will',
  		'flow',
  		'potential',
  		'potentiality',
  		'chi',
  		'intuition',
  		'synchronicity',
  		'wellbeing',
  		'joy',
  		'love',
  		'karma',
  		'life-force',
  		'awareness',
  		'guidance',
  		'transformation',
  		'grace',
  		'divinity',
  		'non-locality',
  		'inseparability',
  		'interconnectedness',
  		'transcendence',
  		'empathy',
  		'insight',
  		'rejuvenation',
  		'ecstasy',
  		'aspiration',
  		'complexity',
  		'serenity',
  	],
    nMassBad: [
  		'turbulence',
  		'pain',
  		'suffering',
  		'stagnation',
  		'desire',
  		'bondage',
  		'greed',
  		'selfishness',
  		'ego',
  		'dogma',
  		'illusion',
  		'delusion',
  		'yearning',
  		'discontinuity',
  		'materialism',
  	],
    nOurPlural: [
  		'souls',
  		'lives',
  		'dreams',
  		'hopes',
  		'bodies',
  		'hearts',
  		'brains',
  		'third eyes',
  		'essences',
  		'chakras',
  	],
    nPath: [
  		'circuit',
  		'mission',
  		'journey',
  		'path',
  		'quest',
  		'vision quest',
  		'story',
  		'myth',
  	],
    nOf: [
  		'quantum leap',
  		'evolution',
  		'spark',
  		'lightning bolt',
  		'reintegration',
  		'vector',
  		'rebirth',
  		'revolution',
  		'wellspring',
  		'fount',
  		'source',
  		'fusion',
  		'canopy',
  		'flow',
  		'network',
  		'current',
  		'transmission',
  		'oasis',
  		'quantum shift',
  		'paradigm shift',
  		'metamorphosis',
  		'harmonizing',
  		'reimagining',
  		'rekindling',
  		'unifying',
  		'osmosis',
  		'vision',
  		'uprising',
  		'explosion',
  	],
    ing: [
  		'flowering',
  		'unfolding',
  		'blossoming',
  		'awakening',
  		'deepening',
  		'refining',
  		'maturing',
  		'evolving',
  		'summoning',
  		'unveiling',
  		'redefining',
  		'condensing',
  		'ennobling',
  	],
    adj: [
  		'enlightened',
  		'zero-point',
  		'quantum',
  		'high-frequency',
  		'Vedic',
  		'non-dual',
  		'conscious',
  		'sentient',
  		'sacred',
  		'infinite',
  		'primordial',
  		'ancient',
  		'powerful',
  		'spiritual',
  		'higher',
  		'advanced',
  		'internal',
  		'sublime',
  		'technological',
  		'dynamic',
  		'life-affirming',
  		'sensual',
  		'unrestricted',
  		'ever-present',
  		'endless',
  		'ethereal',
  		'astral',
  		'cosmic',
  		'spatial',
  		'transformative',
  		'unified',
  		'non-local',
  		'mystical',
  		'divine',
  		'self-aware',
  		'magical',
  		'amazing',
  		'interstellar',
  		'unlimited',
  		'authentic',
  		'angelic',
  		'karmic',
  		'psychic',
  		'pranic',
  		'consciousness-expanding',
  		'perennial',
  		'heroic',
  		'archetypal',
  		'mythic',
  		'intergalatic',
  		'holistic',
  		'joyous',
  		'sublime',
  	],
    adjBig: [
  		'epic',
  		'unimaginable',
  		'colossal',
  		'unfathomable',
  		'magnificent',
  		'enormous',
  		'jaw-dropping',
  		'ecstatic',
  		'powerful',
  		'untold',
  		'astonishing',
  		'incredible',
  		'breathtaking',
  		'staggering',
  	],
    adjWith: [
  		'aglow with',
  		'buzzing with',
  		'beaming with',
  		'full of',
  		'overflowing with',
  		'radiating',
  		'bursting with',
  		'electrified with',
  	],
    adjPrefix: [
  		'ultra-',
  		'supra-',
  		'hyper-',
  		'pseudo-',
  	],
    vtMass: [
  		'inspire',
  		'integrate',
  		'ignite',
  		'discover',
  		'rediscover',
  		'foster',
  		'release',
  		'manifest',
  		'harmonize',
  		'engender',
  		'bring forth',
  		'bring about',
  		'create',
  		'spark',
  		'reveal',
  		'generate',
  		'leverage',
  	],
    vtPerson: [
  		'enlighten',
  		'inspire',
  		'empower',
  		'unify',
  		'strengthen',
  		'recreate',
  		'fulfill',
  		'change',
  		'develop',
  		'heal',
  		'awaken',
  		'synergize',
  		'ground',
  		'bless',
  		'beckon',
  	],
    viPerson: [
  		'exist',
  		'believe',
  		'grow',
  		'live',
  		'dream',
  		'reflect',
  		'heal',
  		'vibrate',
  		'self-actualize',
  	],
    vtDestroy: [
  		'destroy',
  		'eliminate',
  		'shatter',
  		'disrupt',
  		'sabotage',
  		'exterminate',
  		'obliterate',
  		'eradicate',
  		'extinguish',
  		'erase',
  		'confront',
  	],
    nTheXOf: [
  		'richness',
  		'truth',
  		'growth',
  		'nature',
  		'healing',
  		'knowledge',
  	],
    ppPerson: [
  		'awakened',
  		're-energized',
  		'recreated',
  		'reborn',
  		'guided',
  		'aligned',
  	],
    ppThingPrep: [
  		'enveloped in',
  		'transformed into',
  		'nurtured by',
  		'opened by',
  		'immersed in',
  		'engulfed in',
  		'baptized in',
  	],
    fixedAdvP: [
  		'through non-local interactions',
  		'inherent in nature',
  		'at the quantum level',
  		'at the speed of light',
  		'of unfathomable proportions',
  		'on a cosmic scale',
  		'devoid of self',
  		'of the creative act',
  		,
  	],
    fixedAdvPPlace: [
  		'in this dimension',
  		'outside time',
  		'within the Godhead',
  		'at home in the cosmos',
  		,
  	],
    fixedNP: [
  		'expanding wave functions',
  		'superpositions of possibilities',
  		'electromagnetic forces',
  		'electromagnetic resonance',
  		'molecular structures',
  		'atomic ionization',
  		'electrical impulses',
  		'a resonance cascade',
  		'bio-electricity',
  		'ultrasonic energy',
  		'sonar energy',
  		'vibrations',
  		'frequencies',
  		'four-dimensional superstructures',
  		'ultra-sentient particles',
  		'sub-atomic particles',
  		'chaos-driven reactions',
  		'supercharged electrons',
  		'supercharged waveforms',
  		'pulses',
  		'transmissions',
  		'morphogenetic fields',
  		'bio-feedback',
  		'meridians',
  		'morphic resonance',
  	],
    nSubject: [
  		'alternative medicine',
  		'astrology',
  		'tarot',
  		'crystal healing',
  		'the akashic record',
  		'feng shui',
  		'acupuncture',
  		'homeopathy',
  		'aromatherapy',
  		'ayurvedic medicine',
  		'faith healing',
  		'prayer',
  		'astral projection',
  		'Kabala',
  		'reiki',
  		'naturopathy',
  		'numerology',
  		'affirmations',
  		'the Law of Attraction',
  	],
    vOpenUp: [
  		'open up',
  		'give us access to',
  		'enable us to access',
  		'remove the barriers to',
  		'clear a path toward',
  		'let us access',
  		'tap into',
  		'align us with',
  	],
    vTraverse: [
  		'traverse',
  		'walk',
  		'follow',
  		'engage with',
  		'go along',
  		'roam',
  		'navigate',
  		'wander',
  		'embark on',
  	],
  };
}
