import test from 'node:test';
import assert from 'node:assert/strict';
import { discussedTopicsForEvent, eventTopicSummary, normalizeDiscussedTopics, topicLabel } from '../src/lib/call-topics.js';

test('unsuccessful calls never receive discussed topics', () => {
  assert.deepEqual(normalizeDiscussedTopics('No Answer', 'Behavior', ['Homework']), []);
  assert.equal(topicLabel('Behavior', [], 'No Answer'), 'Behavior');
});

test('connected calls default discussed topics to the planned topic and deduplicate', () => {
  assert.deepEqual(normalizeDiscussedTopics('Connected', 'Behavior', ['Behavior', 'Homework', 'Behavior']), ['Behavior', 'Homework']);
  assert.equal(topicLabel('Behavior', ['Behavior', 'Homework'], 'Connected'), 'Behavior, Homework');
});

test('event topic helpers never treat unsuccessful planned topics as discussed', () => {
  assert.deepEqual(discussedTopicsForEvent({ result: 'Busy', plannedTopic: 'Behavior', discussedTopics: ['Behavior'] }), []);
  assert.deepEqual(discussedTopicsForEvent({ result: 'Connected', discussedTopics: ['Homework', 'Progress'] }), ['Homework', 'Progress']);
});

test('event topic summary separates planned and discussed topics by outcome', () => {
  assert.deepEqual(eventTopicSummary({ result: 'No Answer', plannedTopic: 'Behavior', discussedTopics: ['Homework'] }), {
    planned: 'Behavior',
    discussed: [],
  });
  assert.deepEqual(eventTopicSummary({ result: 'Connected', plannedTopic: 'Behavior', discussedTopics: ['Behavior', 'Homework'] }), {
    planned: 'Behavior',
    discussed: ['Behavior', 'Homework'],
  });
});
